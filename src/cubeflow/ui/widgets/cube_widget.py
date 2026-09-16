import math

from PySide6.QtCore import QPointF, Qt, QTimer
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

from cubeflow.cube.cube_state import FACE_NORMALS, CubeState, Vector3
from cubeflow.cube.enums import Face

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
_ANIMATION_STEPS_TOTAL = 12

_INITIAL_ROTATION_X_DEG = -35.264
_INITIAL_ROTATION_Y_DEG = 45


def _rotate(vertex: Vector3, rotation_x: float, rotation_y: float) -> tuple[float, float, float]:
    x, y, z = vertex

    y_rotated = y * math.cos(rotation_x) - z * math.sin(rotation_x)
    z_rotated = y * math.sin(rotation_x) + z * math.cos(rotation_x)

    y = y_rotated
    z = z_rotated

    x_rotated = x * math.cos(rotation_y) + z * math.sin(rotation_y)
    z_rotated2 = -x * math.sin(rotation_y) + z * math.cos(rotation_y)

    return x_rotated, y, z_rotated2


def _visible_faces(rotation_x: float, rotation_y: float) -> set[Face]:
    depths = {
        face: _rotate(normal, rotation_x, rotation_y)[2]
        for face, normal in FACE_NORMALS.items()
    }

    ranked = sorted(depths, key=lambda face: depths[face], reverse=True)

    return set(ranked[:3])


def _build_camera_presets() -> list[tuple[float, float, set[Face]]]:
    presets = []

    for rx_deg in (-35.264, 35.264):
        for ry_deg in (45, 135, 225, 315):
            rx = math.radians(rx_deg)
            ry = math.radians(ry_deg)

            presets.append((rx, ry, _visible_faces(rx, ry)))

    return presets


_CAMERA_PRESETS = _build_camera_presets()


def _shade(color: QColor, brightness: float) -> QColor:
    return QColor(
        int(color.red() * brightness),
        int(color.green() * brightness),
        int(color.blue() * brightness),
    )


class CubeWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setMinimumHeight(300)

        self.cube_state = CubeState()
        self.highlighted_face: Face | None = None

        self.rotation_x = math.radians(_INITIAL_ROTATION_X_DEG)
        self.rotation_y = math.radians(_INITIAL_ROTATION_Y_DEG)

        self._start_rotation = (self.rotation_x, self.rotation_y)
        self._target_rotation = (self.rotation_x, self.rotation_y)
        self._animation_step = 0

        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._advance_animation)

        self._dragging = False
        self._last_mouse_pos = QPointF()

        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._animation_timer.stop()
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

        self._target_rotation = (self.rotation_x, self.rotation_y)

        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def set_state(self, cube_state: CubeState) -> None:
        self.cube_state = cube_state
        self.update()

    def set_highlighted_face(self, face: Face | None, animate: bool = True) -> None:
        self.highlighted_face = face

        if face is not None:
            self._point_camera_at(face, animate)

        self.update()

    def _point_camera_at(self, face: Face, animate: bool) -> None:
        current_visible = _visible_faces(*self._target_rotation)

        candidates = [
            preset
            for preset in _CAMERA_PRESETS
            if face in preset[2]
        ]

        best = max(
            candidates,
            key=lambda preset: len(preset[2] & current_visible),
        )

        target = (best[0], best[1])

        if target == self._target_rotation:
            return

        self._target_rotation = target

        if animate:
            self._start_rotation = (self.rotation_x, self.rotation_y)
            self._animation_step = 0
            self._animation_timer.start(_ANIMATION_FRAME_INTERVAL_MS)
        else:
            self.rotation_x, self.rotation_y = target

    def _advance_animation(self) -> None:
        self._animation_step += 1
        t = min(1.0, self._animation_step / _ANIMATION_STEPS_TOTAL)

        eased = t * t * (3 - 2 * t)

        start_x, start_y = self._start_rotation
        target_x, target_y = self._target_rotation

        self.rotation_x = start_x + (target_x - start_x) * eased
        self.rotation_y = start_y + (target_y - start_y) * eased

        self.update()

        if t >= 1.0:
            self._animation_timer.stop()

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

        depth = _rotate(
            FACE_NORMALS[face], self.rotation_x, self.rotation_y
        )[2]
        brightness = max(0.0, min(1.0, _SHADING_BASE + depth * _SHADING_DEPTH_FACTOR))

        for row in range(3):
            for col in range(3):
                position = [0, 0, 0]
                position[fixed_axis] = fixed_value
                position[axis_a] = row - 1
                position[axis_b] = col - 1

                normal = [0, 0, 0]
                normal[fixed_axis] = fixed_value

                color = self.cube_state.get_sticker(
                    tuple(position), tuple(normal)
                )

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
                )

                painter.setBrush(_shade(FACE_COLORS[color], brightness))
                painter.setPen(QPen(STICKER_BORDER_COLOR, _STICKER_BORDER_WIDTH))
                painter.drawPolygon(polygon)

        if face == self.highlighted_face:
            self._draw_face_outline(painter, face)

    def _draw_face_outline(self, painter: QPainter, face: Face) -> None:
        fixed_axis, fixed_value, axis_a, axis_b = FACE_GRID_AXES[face]

        polygon = self._project_face_polygon(
            fixed_axis, fixed_value, axis_a, axis_b, _OUTLINE_BOUNDS
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
    ) -> QPolygonF:
        polygon = QPolygonF()

        for a, b in corners:
            corner = [0.0, 0.0, 0.0]
            corner[fixed_axis] = fixed_value
            corner[axis_a] = a
            corner[axis_b] = b

            rotated = _rotate(tuple(corner), self.rotation_x, self.rotation_y)
            polygon.append(self._project_vertex(rotated))

        return polygon

    def _project_vertex(self, vertex: tuple[float, float, float]) -> QPointF:
        x, y, _ = vertex
        scale = min(self.width(), self.height()) * _PROJECTION_SCALE

        screen_x = self.width() / 2 + x * scale
        screen_y = self.height() / 2 - y * scale

        return QPointF(screen_x, screen_y)
