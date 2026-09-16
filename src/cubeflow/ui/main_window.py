from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from cubeflow.cube.cube_state import CubeState
from cubeflow.cube.enums import Face, Turn
from cubeflow.cube.move import Move
from cubeflow.cube.scramble_generator import ScrambleGenerator
from cubeflow.ui.widgets.cube_widget import CubeWidget
from cubeflow.ui.widgets.navigation_widget import NavigationWidget
from cubeflow.ui.widgets.scramble_widget import ScrambleWidget

FACE_NAMES_DE = {
    Face.UP: "Oben",
    Face.DOWN: "Unten",
    Face.LEFT: "Links",
    Face.RIGHT: "Rechts",
    Face.FRONT: "Vorne",
    Face.BACK: "Hinten",
}

TURN_NAMES_DE = {
    Turn.CLOCKWISE: "90° im Uhrzeigersinn",
    Turn.COUNTERCLOCKWISE: "90° gegen den Uhrzeigersinn",
    Turn.DOUBLE: "180°",
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("CubeFlow")
        self.resize(1000, 700)

        self.scramble_generator = ScrambleGenerator()
        self.current_step = 0
        self.setup_ui()

    def setup_ui(self) -> None:
        self.scramble = self.scramble_generator.generate()

        self.scramble_widget = ScrambleWidget()
        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.cube_widget = CubeWidget()
        self.navigation_widget = NavigationWidget()

        self.navigation_widget.next_clicked.connect(self.next_step)
        self.navigation_widget.previous_clicked.connect(self.previous_step)

        central_widget = QWidget()

        layout = QVBoxLayout(central_widget)

        layout.addWidget(self.scramble_widget)
        layout.addWidget(self.status_label)
        layout.addWidget(self.cube_widget, 1)
        layout.addWidget(self.navigation_widget)

        self.setCentralWidget(central_widget)

        self.update_view(animate=False)

    def next_step(self) -> None:
        if self.current_step < len(self.scramble):
            self.current_step += 1
            self.update_view(animate=True)

    def previous_step(self) -> None:
        if self.current_step > 0:
            self.current_step -= 1
            self.update_view(animate=True)

    def update_view(self, animate: bool) -> None:
        state = CubeState()

        for move in self.scramble[: self.current_step]:
            state.apply_move(move)

        self.cube_widget.set_state(state)

        pending_move = None

        if self.current_step < len(self.scramble):
            pending_move = self.scramble[self.current_step]

        self.cube_widget.set_highlighted_face(
            pending_move.face if pending_move else None,
            animate=animate,
        )

        self.scramble_widget.set_moves(
            self.scramble,
            self.current_step if pending_move else None,
        )

        self.status_label.setText(self._status_text(pending_move))

        self.navigation_widget.set_navigation_enabled(
            has_previous=self.current_step > 0,
            has_next=self.current_step < len(self.scramble),
        )

    def _status_text(self, pending_move: Move | None) -> str:
        step_info = f"Schritt {self.current_step} / {len(self.scramble)}"

        if pending_move is None:
            return f"{step_info} — Würfel fertig verdreht"

        face_name = FACE_NAMES_DE[pending_move.face]
        turn_name = TURN_NAMES_DE[pending_move.turn]

        return (
            f"{step_info} — Nächster Zug: {pending_move} "
            f"({face_name}, {turn_name})"
        )
