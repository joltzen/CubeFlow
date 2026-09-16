from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from cubeflow.cube.move import Move

_HIGHLIGHT_STYLE = (
    "background-color: #00e5ff; color: #000000; "
    "padding: 2px 4px; border-radius: 4px;"
)


class ScrambleWidget(QWidget):
    def __init__(self, scramble_text: str = "") -> None:
        super().__init__()

        self.scramble_label = QLabel(scramble_text)
        self.scramble_label.setObjectName("scrambleLabel")
        self.scramble_label.setTextFormat(Qt.TextFormat.RichText)

        self.scramble_label.setAlignment(Qt.AlignCenter)
        self.scramble_label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.scramble_label)

        self.setLayout(layout)

    def set_scramble(self, scramble_text: str) -> None:
        self.scramble_label.setText(scramble_text)

    def set_moves(self, moves: list[Move], highlight_index: int | None) -> None:
        tokens = []

        for index, move in enumerate(moves):
            text = str(move)

            if index == highlight_index:
                tokens.append(f'<span style="{_HIGHLIGHT_STYLE}">{text}</span>')
            else:
                tokens.append(text)

        self.scramble_label.setText(" ".join(tokens))