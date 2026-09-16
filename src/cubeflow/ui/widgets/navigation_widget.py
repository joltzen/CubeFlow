from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

_SPEED_STEPS = [160, 130, 100, 60, 30]
_SPEED_LABELS = ["Sehr langsam", "Langsam", "Normal", "Schnell", "Sehr schnell"]
_DEFAULT_SPEED_INDEX = 2


class NavigationWidget(QWidget):
    next_clicked = Signal()
    previous_clicked = Signal()
    new_scramble_clicked = Signal()
    auto_scramble_clicked = Signal()
    speed_changed = Signal(int)

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

        self.auto_scramble_button = QPushButton("Automatisch scrambeln")
        self.auto_scramble_button.setObjectName("autoScrambleButton")
        self.auto_scramble_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.speed_caption = QLabel("Geschwindigkeit:")
        self.speed_caption.setObjectName("speedCaption")

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setObjectName("speedSlider")
        self.speed_slider.setMinimum(0)
        self.speed_slider.setMaximum(len(_SPEED_STEPS) - 1)
        self.speed_slider.setValue(_DEFAULT_SPEED_INDEX)
        self.speed_slider.setFixedWidth(160)
        self.speed_slider.setCursor(Qt.CursorShape.PointingHandCursor)

        self.speed_label = QLabel(_SPEED_LABELS[_DEFAULT_SPEED_INDEX])
        self.speed_label.setObjectName("speedLabel")
        self.speed_label.setFixedWidth(90)

        self.previous_button.clicked.connect(self.previous_clicked.emit)
        self.next_button.clicked.connect(self.next_clicked.emit)
        self.new_scramble_button.clicked.connect(self.new_scramble_clicked.emit)
        self.auto_scramble_button.clicked.connect(self.auto_scramble_clicked.emit)
        self.speed_slider.valueChanged.connect(self._on_speed_slider_changed)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.previous_button)
        buttons_layout.addWidget(self.next_button)
        buttons_layout.addStretch()

        secondary_layout = QHBoxLayout()
        secondary_layout.addStretch()
        secondary_layout.addWidget(self.new_scramble_button)
        secondary_layout.addWidget(self.auto_scramble_button)
        secondary_layout.addStretch()

        speed_layout = QHBoxLayout()
        speed_layout.addStretch()
        speed_layout.addWidget(self.speed_caption)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        speed_layout.addStretch()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.addWidget(self.progress_bar)
        layout.addLayout(buttons_layout)
        layout.addLayout(secondary_layout)
        layout.addLayout(speed_layout)

        self.setLayout(layout)

    def _on_speed_slider_changed(self, index: int) -> None:
        self.speed_label.setText(_SPEED_LABELS[index])
        self.speed_changed.emit(_SPEED_STEPS[index])

    def set_navigation_enabled(self, has_previous: bool, has_next: bool) -> None:
        self.previous_button.setEnabled(has_previous)
        self.next_button.setEnabled(has_next)

    def set_auto_scramble_enabled(self, enabled: bool) -> None:
        self.auto_scramble_button.setEnabled(enabled)

    def set_auto_scrambling(self, active: bool) -> None:
        self.auto_scramble_button.setText("Stopp" if active else "Automatisch scrambeln")
        self.auto_scramble_button.setProperty("active", active)
        self.auto_scramble_button.style().unpolish(self.auto_scramble_button)
        self.auto_scramble_button.style().polish(self.auto_scramble_button)

    def set_progress(self, current_step: int, total_steps: int) -> None:
        self.progress_bar.setRange(0, total_steps)
        self.progress_bar.setValue(current_step)