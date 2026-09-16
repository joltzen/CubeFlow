import math
from dataclasses import dataclass

from PySide6.QtCore import QPointF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import QWidget

from cubeflow.cube.cube_state import FACE_NORMALS, CubeState, Vector3, face_axis
from cubeflow.cube.enums import Face, Turn
from cubeflow.cube.move import Move

FACE_COLORS: dict[Face, QColor] = {
    Face.UP: QColor("white"),
    Face.DOWN: QColor("yellow"),
    Face.FRONT: QColor("green"),
    Face.BACK: QColor("blue"),
    Face.LEFT: QColor("orange"),
    Face.RIGHT: QColor("red"),
}

HIGHLIGHT_COLOR = QColor("#00e5ff")
BACKGROUND_COLOR = QColor("#202020")
STICKER_BORDER_COLOR = QColor("black")

FACE_GRID_AXES: dict[Face, tuple[int, int, int, int]] = {
    Face.RIGHT: (0, 1, 1, 2),
    Face.LEFT: (0, -1, 1, 2),
    Face.UP: (1, 1, 0, 2),
    Face.DOWN: (1, -1, 0, 2),
    Face.FRONT: (2, 1, 0, 1),
    Face.BACK: (2, -1, 0, 1),
}

_CELL_BOUNDS = [-1.0, -1 / 3, 1 / 3, 1.0]
_OUTLINE_BOUNDS = ((-1, -1), (1, -1), (1, 1), (-1, 1))

_BACKGROUND_CORNER_RADIUS = 16
_STICKER_BORDER_WIDTH = 2
_HIGHLIGHT_BORDER_WIDTH = 5

_SHADING_BASE = 0.5
_SHADING_DEPTH_FACTOR = 0.7

_PROJECTION_SCALE = 0.28

_DEGREES_PER_PIXEL = 0.4
_ANIMATION_FRAME_INTERVAL_MS = 16
_LAYER_ANIMATION_STEPS_TOTAL = 34

_INITIAL_ROTATION_X_DEG = -35.264
_INITIAL_ROTATION_Y_DEG = 45

_QUARTER_TURN_DEG = 90

_SIGNED_REPEATS: dict[Turn, int] = {
    Turn.CLOCKWISE: 1,
    Turn.COUNTERCLOCKWISE: -1,
    Turn.DOUBLE: 2,
}


def _rotate(vertex: Vector3, rotation_x: float, rotation_y: float) -> tuple[float, float, float]:
    x, y, z = vertex

    y_rotated = y * math.cos(rotation_x) - z * math.sin(rotation_x)
    z_rotated = y * math.sin(rotation_x) + z * math.cos(rotation_x)

    y = y_rotated
    z = z_rotated

    x_rotated = x * math.cos(rotation_y) + z * math.sin(rotation_y)
    z_rotated2 = -x * math.sin(rotation_y) + z * math.cos(rotation_y)

    return x_rotated, y, z_rotated2


def _rotate_about_axis(vertex: Vector3, axis: int, angle: float) -> tuple[float, float, float]:
    x, y, z = (float(component) for component in vertex)
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    if axis == 0:
        return (x, y * cos_a - z * sin_a, y * sin_a + z * cos_a)
    if axis == 1:
        return (x * cos_a + z * sin_a, y, -x * sin_a + z * cos_a)
    return (x * cos_a - y * sin_a, x * sin_a + y * cos_a, z)


def _shade(color: QColor, brightness: float) -> QColor:
    return QColor(
        int(color.red() * brightness),
        int(color.green() * brightness),
        int(color.blue() * brightness),
    )


def _smoothstep(t: float) -> float:
    return t * t * (3 - 2 * t)


def _turn_angle(move: Move) -> tuple[int, int, float]:
    axis, layer_value = face_axis(move.face)
    quarter_angle_deg = -_QUARTER_TURN_DEG * layer_value
    signed_repeats = _SIGNED_REPEATS[move.turn]

    return axis, layer_value, math.radians(quarter_angle_deg * signed_repeats)


@dataclass
class _LayerAnimation:
    axis: int
    layer_value: int
    target_angle: float
    state_before: CubeState
    current_angle: float = 0.0


class CubeWidget(QWidget):
    turn_finished = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.setMinimumHeight(300)

        self.cube_state = CubeState()
        self.highlighted_face: Face | None = None

        self.rotation_x = math.radians(_INITIAL_ROTATION_X_DEG)
        self.rotation_y = math.radians(_INITIAL_ROTATION_Y_DEG)

        self._layer_animation: _LayerAnimation | None = None
        self._layer_animation_step = 0
        self._pending_state_after: CubeState | None = None

        self._layer_animation_timer = QTimer(self)
        self._layer_animation_timer.timeout.connect(self._advance_layer_animation)

        self._dragging = False
        self._last_mouse_pos = QPointF()

        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._dragging:
            return

        pos = event.position()
        delta = pos - self._last_mouse_pos
        self._last_mouse_pos = pos

        self.rotation_y += math.radians(delta.x() * _DEGREES_PER_PIXEL)
        self.rotation_x -= math.radians(delta.y() * _DEGREES_PER_PIXEL)

        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def set_state(self, cube_state: CubeState) -> None:
        self.cube_state = cube_state
        self.update()

    def animate_turn(self, state_before: CubeState, move: Move, state_after: CubeState) -> None:
        self._finish_layer_animation_immediately()

        axis, layer_value, target_angle = _turn_angle(move)

        self._layer_animation = _LayerAnimation(
            axis=axis,
            layer_value=layer_value,
            target_angle=target_angle,
            state_before=state_before,
        )
        self._pending_state_after = state_after
        self.cube_state = state_before

        self._layer_animation_step = 0
        self._layer_animation_timer.start(_ANIMATION_FRAME_INTERVAL_MS)

        self.set_highlighted_face(move.face)

    def _finish_layer_animation_immediately(self) -> None:
        if self._layer_animation is None:
            return

        self._layer_animation_timer.stop()
        self.cube_state = self._pending_state_after
        self._layer_animation = None
        self._pending_state_after = None
        self.turn_finished.emit()

    def _advance_layer_animation(self) -> None:
        animation = self._layer_animation
        assert animation is not None

        self._layer_animation_step += 1
        t = min(1.0, self._layer_animation_step / _LAYER_ANIMATION_STEPS_TOTAL)

        animation.current_angle = animation.target_angle * _smoothstep(t)
        self.update()

        if t >= 1.0:
            self._finish_layer_animation_immediately()

    def set_highlighted_face(self, face: Face | None) -> None:
        self.highlighted_face = face
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        background_path = QPainterPath()
        background_path.addRoundedRect(
            0,
            0,
            self.width(),
            self.height(),
            _BACKGROUND_CORNER_RADIUS,
            _BACKGROUND_CORNER_RADIUS,
        )
        painter.fillPath(background_path, BACKGROUND_COLOR)
        painter.setClipPath(background_path)

        face_depths = []

        for face, normal in FACE_NORMALS.items():
            depth = _rotate(normal, self.rotation_x, self.rotation_y)[2]
            face_depths.append((depth, face))

        face_depths.sort(key=lambda item: item[0])

        for _, face in face_depths:
            self._draw_face(painter, face)

        painter.end()

    def _draw_face(self, painter: QPainter, face: Face) -> None:
        fixed_axis, fixed_value, axis_a, axis_b = FACE_GRID_AXES[face]

        for row in range(3):
            for col in range(3):
                position = [0, 0, 0]
                position[fixed_axis] = fixed_value
                position[axis_a] = row - 1
                position[axis_b] = col - 1

                normal = [0, 0, 0]
                normal[fixed_axis] = fixed_value

                turn_angle = self._sticker_turn_angle(position)
                state = self.cube_state if turn_angle == 0.0 else self._layer_animation.state_before
                color = state.get_sticker(tuple(position), tuple(normal))

                polygon = self._project_face_polygon(
                    fixed_axis,
                    fixed_value,
                    axis_a,
                    axis_b,
                    (
                        (_CELL_BOUNDS[row], _CELL_BOUNDS[col]),
                        (_CELL_BOUNDS[row + 1], _CELL_BOUNDS[col]),
                        (_CELL_BOUNDS[row + 1], _CELL_BOUNDS[col + 1]),
                        (_CELL_BOUNDS[row], _CELL_BOUNDS[col + 1]),
                    ),
                    turn_angle,
                )

                brightness = self._sticker_brightness(tuple(normal), turn_angle)
                painter.setBrush(_shade(FACE_COLORS[color], brightness))
                painter.setPen(QPen(STICKER_BORDER_COLOR, _STICKER_BORDER_WIDTH))
                painter.drawPolygon(polygon)

        if face == self.highlighted_face:
            self._draw_face_outline(painter, face)

    def _sticker_turn_angle(self, position: list[int]) -> float:
        animation = self._layer_animation

        if animation is None:
            return 0.0

        return self._face_turn_angle(animation.axis, position[animation.axis])

    def _face_turn_angle(self, fixed_axis: int, fixed_value: int) -> float:
        animation = self._layer_animation

        if animation is None or fixed_axis != animation.axis or fixed_value != animation.layer_value:
            return 0.0

        return animation.current_angle

    def _sticker_brightness(self, normal: Vector3, turn_angle: float) -> float:
        oriented_normal = (
            normal
            if turn_angle == 0.0
            else _rotate_about_axis(normal, self._layer_animation.axis, turn_angle)
        )
        depth = _rotate(oriented_normal, self.rotation_x, self.rotation_y)[2]

        return max(0.0, min(1.0, _SHADING_BASE + depth * _SHADING_DEPTH_FACTOR))

    def _draw_face_outline(self, painter: QPainter, face: Face) -> None:
        fixed_axis, fixed_value, axis_a, axis_b = FACE_GRID_AXES[face]
        turn_angle = self._face_turn_angle(fixed_axis, fixed_value)

        polygon = self._project_face_polygon(
            fixed_axis, fixed_value, axis_a, axis_b, _OUTLINE_BOUNDS, turn_angle
        )

        painter.setBrush(QColor(0, 0, 0, 0))
        painter.setPen(QPen(HIGHLIGHT_COLOR, _HIGHLIGHT_BORDER_WIDTH))
        painter.drawPolygon(polygon)

    def _project_face_polygon(
        self,
        fixed_axis: int,
        fixed_value: int,
        axis_a: int,
        axis_b: int,
        corners: tuple[tuple[float, float], ...],
        turn_angle: float = 0.0,
    ) -> QPolygonF:
        polygon = QPolygonF()

        for a, b in corners:
            corner = [0.0, 0.0, 0.0]
            corner[fixed_axis] = fixed_value
            corner[axis_a] = a
            corner[axis_b] = b

            if turn_angle != 0.0:
                corner = list(
                    _rotate_about_axis(tuple(corner), self._layer_animation.axis, turn_angle)
                )

            rotated = _rotate(tuple(corner), self.rotation_x, self.rotation_y)
            polygon.append(self._project_vertex(rotated))

        return polygon

    def _project_vertex(self, vertex: tuple[float, float, float]) -> QPointF:
        x, y, _ = vertex
        scale = min(self.width(), self.height()) * _PROJECTION_SCALE

        screen_x = self.width() / 2 + x * scale
        screen_y = self.height() / 2 - y * scale

        return QPointF(screen_x, screen_y)
