from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class NavigationWidget(QWidget):
    next_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.next_button = QPushButton("Weiter")
        self.next_button.setObjectName("nextButton")

        self.next_button.clicked.connect(self.next_clicked.emit)

        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.next_button)
        layout.addStretch()

        self.setLayout(layout)