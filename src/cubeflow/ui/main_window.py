from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from cubeflow.cube.cube_state import CubeState, build_state
from cubeflow.cube.enums import INVERSE_TURN, Face, Turn
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
        self.resize(1080, 760)

        self.scramble_generator = ScrambleGenerator()
        self._auto_scrambling = False
        self.setup_ui()

    def setup_ui(self) -> None:
        self.scramble_widget = ScrambleWidget()
        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.cube_widget = CubeWidget()
        self.navigation_widget = NavigationWidget()

        self.navigation_widget.next_clicked.connect(self.next_step)
        self.navigation_widget.previous_clicked.connect(self.previous_step)
        self.navigation_widget.new_scramble_clicked.connect(self.start_new_scramble)
        self.navigation_widget.auto_scramble_clicked.connect(self.toggle_auto_scramble)
        self.navigation_widget.speed_changed.connect(self.cube_widget.set_turn_speed)
        self.cube_widget.turn_finished.connect(self._on_turn_finished)

        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        layout.addWidget(self.scramble_widget)
        layout.addWidget(self.status_label)
        layout.addWidget(self.cube_widget, 1)
        layout.addWidget(self.navigation_widget)

        self.setCentralWidget(central_widget)

        self.start_new_scramble()

    def start_new_scramble(self) -> None:
        self._stop_auto_scramble()

        self.scramble = self.scramble_generator.generate()
        self.current_step = 0

        self.cube_widget.reset_to_solved()
        self._preview_pending_move()
        self._update_status_ui()

    def toggle_auto_scramble(self) -> None:
        if self._auto_scrambling:
            self._stop_auto_scramble()
        else:
            self._start_auto_scramble()

    def _start_auto_scramble(self) -> None:
        if self.current_step >= len(self.scramble):
            return

        self._auto_scrambling = True
        self.navigation_widget.set_auto_scrambling(True)
        self.next_step()

    def _stop_auto_scramble(self) -> None:
        if not self._auto_scrambling:
            return

        self._auto_scrambling = False
        self.navigation_widget.set_auto_scrambling(False)
        self._update_status_ui()

    def _on_turn_finished(self) -> None:
        self._preview_pending_move()

        if not self._auto_scrambling:
            return

        if self.current_step < len(self.scramble):
            self.next_step()
        else:
            self._stop_auto_scramble()

    def next_step(self) -> None:
        if self.current_step >= len(self.scramble):
            return

        move = self.scramble[self.current_step]
        state_before = self._state_at(self.current_step)

        self.current_step += 1
        state_after = self._state_at(self.current_step)

        self.cube_widget.animate_turn(state_before, move, state_after)
        self._update_status_ui()

    def previous_step(self) -> None:
        if self.current_step <= 0:
            return

        undone_move = self.scramble[self.current_step - 1]
        state_before = self._state_at(self.current_step)

        self.current_step -= 1
        state_after = self._state_at(self.current_step)

        reverse_move = Move(undone_move.face, INVERSE_TURN[undone_move.turn])
        self.cube_widget.animate_turn(state_before, reverse_move, state_after)
        self._update_status_ui()

    def _state_at(self, step: int) -> CubeState:
        return build_state(self.scramble[:step])

    def _pending_move(self) -> Move | None:
        if self.current_step < len(self.scramble):
            return self.scramble[self.current_step]

        return None

    def _preview_pending_move(self) -> None:
        pending_move = self._pending_move()

        self.cube_widget.set_highlighted_face(
            pending_move.face if pending_move else None
        )

    def _update_status_ui(self) -> None:
        pending_move = self._pending_move()

        self.scramble_widget.set_moves(
            self.scramble,
            self.current_step if pending_move else None,
        )

        self.status_label.setText(self._status_text(pending_move))
        self._set_status_state("done" if pending_move is None else "pending")

        self.navigation_widget.set_navigation_enabled(
            has_previous=self.current_step > 0 and not self._auto_scrambling,
            has_next=self.current_step < len(self.scramble) and not self._auto_scrambling,
        )
        self.navigation_widget.set_auto_scramble_enabled(
            self._auto_scrambling or self.current_step < len(self.scramble)
        )
        self.navigation_widget.set_progress(self.current_step, len(self.scramble))

    def _set_status_state(self, state: str) -> None:
        self.status_label.setProperty("state", state)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

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
