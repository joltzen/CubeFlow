import math

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPolygonF
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

FACE_GRID_AXES: dict[Face, tuple[int, int, int, int]] = {
    Face.RIGHT: (0, 1, 1, 2),
    Face.LEFT: (0, -1, 1, 2),
    Face.UP: (1, 1, 0, 2),
    Face.DOWN: (1, -1, 0, 2),
    Face.FRONT: (2, 1, 0, 1),
    Face.BACK: (2, -1, 0, 1),
}

_CELL_BOUNDS = [-1.0, -1 / 3, 1 / 3, 1.0]


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

        self.rotation_x = math.radians(-35.264)
        self.rotation_y = math.radians(45)

        self._start_rotation = (self.rotation_x, self.rotation_y)
        self._target_rotation = (self.rotation_x, self.rotation_y)
        self._animation_step = 0
        self._animation_steps_total = 12

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

        degrees_per_pixel = 0.4

        self.rotation_y += math.radians(delta.x() * degrees_per_pixel)
        self.rotation_x -= math.radians(delta.y() * degrees_per_pixel)

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
            self._animation_timer.start(16)
        else:
            self.rotation_x, self.rotation_y = target

    def _advance_animation(self) -> None:
        self._animation_step += 1
        t = min(1.0, self._animation_step / self._animation_steps_total)

        eased = t * t * (3 - 2 * t)

        start_x, start_y = self._start_rotation
        target_x, target_y = self._target_rotation

        self.rotation_x = start_x + (target_x - start_x) * eased
        self.rotation_y = start_y + (target_y - start_y) * eased

        self.update()

        if t >= 1.0:
            self._animation_timer.stop()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor("#202020"))

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
        brightness = max(0.0, min(1.0, 0.5 + depth * 0.7))

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

                polygon = QPolygonF()

                for a, b in (
                    (_CELL_BOUNDS[row], _CELL_BOUNDS[col]),
                    (_CELL_BOUNDS[row + 1], _CELL_BOUNDS[col]),
                    (_CELL_BOUNDS[row + 1], _CELL_BOUNDS[col + 1]),
                    (_CELL_BOUNDS[row], _CELL_BOUNDS[col + 1]),
                ):
                    corner = [0.0, 0.0, 0.0]
                    corner[fixed_axis] = fixed_value
                    corner[axis_a] = a
                    corner[axis_b] = b

                    rotated = _rotate(
                        tuple(corner), self.rotation_x, self.rotation_y
                    )
                    polygon.append(self.project_vertex(rotated))

                painter.setBrush(_shade(FACE_COLORS[color], brightness))
                painter.setPen(QPen(QColor("black"), 2))
                painter.drawPolygon(polygon)

        if face == self.highlighted_face:
            self._draw_face_outline(painter, face)

    def _draw_face_outline(self, painter: QPainter, face: Face) -> None:
        fixed_axis, fixed_value, axis_a, axis_b = FACE_GRID_AXES[face]

        polygon = QPolygonF()

        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            corner = [0.0, 0.0, 0.0]
            corner[fixed_axis] = fixed_value
            corner[axis_a] = a
            corner[axis_b] = b

            rotated = _rotate(tuple(corner), self.rotation_x, self.rotation_y)
            polygon.append(self.project_vertex(rotated))

        painter.setBrush(QColor(0, 0, 0, 0))
        painter.setPen(QPen(HIGHLIGHT_COLOR, 5))
        painter.drawPolygon(polygon)

    def project_vertex(
        self,
        vertex: tuple[float, float, float],
    ) -> QPointF:

        x, y, _ = vertex
        scale = min(self.width(), self.height()) * 0.28

        screen_x = self.width() / 2 + x * scale
        screen_y = self.height() / 2 - y * scale

        return QPointF(
            screen_x,
            screen_y,
        )
