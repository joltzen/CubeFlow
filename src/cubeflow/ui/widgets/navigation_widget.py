from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class NavigationWidget(QWidget):
    next_clicked = Signal()
    previous_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.previous_button = QPushButton("Zurück")
        self.previous_button.setObjectName("prevButton")

        self.next_button = QPushButton("Weiter")
        self.next_button.setObjectName("nextButton")

        self.previous_button.clicked.connect(self.previous_clicked.emit)
        self.next_button.clicked.connect(self.next_clicked.emit)

        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.previous_button)
        layout.addWidget(self.next_button)
        layout.addStretch()

        self.setLayout(layout)

    def set_navigation_enabled(self, has_previous: bool, has_next: bool) -> None:
        self.previous_button.setEnabled(has_previous)
        self.next_button.setEnabled(has_next)