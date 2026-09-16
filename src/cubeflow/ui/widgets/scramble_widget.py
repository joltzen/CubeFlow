from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ScrambleWidget(QWidget):
    def __init__(self, scramble_text: str) -> None:
        super().__init__()

        self.scramble_label = QLabel(scramble_text)
        self.scramble_label.setObjectName("scrambleLabel")

        self.scramble_label.setAlignment(Qt.AlignCenter)
        self.scramble_label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.scramble_label)

        self.setLayout(layout)

    def set_scramble(self, scramble_text: str) -> None:
        self.scramble_label.setText(scramble_text)