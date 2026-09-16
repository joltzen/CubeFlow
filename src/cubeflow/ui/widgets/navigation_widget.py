from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class NavigationWidget(QWidget):
    next_clicked = Signal()
    previous_clicked = Signal()
    new_scramble_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("stepProgress")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        self.previous_button = QPushButton("‹  Zurück")
        self.previous_button.setObjectName("prevButton")
        self.previous_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.next_button = QPushButton("Weiter  ›")
        self.next_button.setObjectName("nextButton")
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.new_scramble_button = QPushButton("Neuer Scramble")
        self.new_scramble_button.setObjectName("newScrambleButton")
        self.new_scramble_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.previous_button.clicked.connect(self.previous_clicked.emit)
        self.next_button.clicked.connect(self.next_clicked.emit)
        self.new_scramble_button.clicked.connect(self.new_scramble_clicked.emit)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.previous_button)
        buttons_layout.addWidget(self.next_button)
        buttons_layout.addStretch()

        new_scramble_layout = QHBoxLayout()
        new_scramble_layout.addStretch()
        new_scramble_layout.addWidget(self.new_scramble_button)
        new_scramble_layout.addStretch()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.addWidget(self.progress_bar)
        layout.addLayout(buttons_layout)
        layout.addLayout(new_scramble_layout)

        self.setLayout(layout)

    def set_navigation_enabled(self, has_previous: bool, has_next: bool) -> None:
        self.previous_button.setEnabled(has_previous)
        self.next_button.setEnabled(has_next)

    def set_progress(self, current_step: int, total_steps: int) -> None:
        self.progress_bar.setRange(0, total_steps)
        self.progress_bar.setValue(current_step)