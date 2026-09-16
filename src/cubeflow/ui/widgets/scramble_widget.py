from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from cubeflow.cube.move import Move

_HIGHLIGHT_STYLE = (
    "background-color: #00e5ff; color: #06232a; "
    "padding: 2px 6px; border-radius: 6px;"
)
_DONE_STYLE = "color: #4a4b58; text-decoration: line-through;"


class ScrambleWidget(QWidget):
    def __init__(self, scramble_text: str = "") -> None:
        super().__init__()

        self.setObjectName("scrambleCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

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
        done_count = highlight_index if highlight_index is not None else len(moves)

        tokens = []

        for index, move in enumerate(moves):
            text = str(move)

            if index == highlight_index:
                tokens.append(f'<span style="{_HIGHLIGHT_STYLE}">{text}</span>')
            elif index < done_count:
                tokens.append(f'<span style="{_DONE_STYLE}">{text}</span>')
            else:
                tokens.append(text)

        self.scramble_label.setText(" ".join(tokens))