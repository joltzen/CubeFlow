from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from cubeflow.cube.scramble_generator import ScrambleGenerator
from cubeflow.ui.widgets.navigation_widget import NavigationWidget
from cubeflow.ui.widgets.scramble_widget import ScrambleWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("CubeFlow")
        self.resize(1000, 700)

        self.scramble_generator = ScrambleGenerator()

        self.setup_ui()

    def setup_ui(self) -> None:
        self.scramble = self.scramble_generator.generate()

        scramble_text = " ".join(
            str(move) for move in self.scramble
        )

        self.scramble_widget = ScrambleWidget(scramble_text)
        self.navigation_widget = NavigationWidget()

        self.navigation_widget.next_clicked.connect(self.next_step)

        central_widget = QWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.scramble_widget)
        layout.addStretch()
        layout.addWidget(self.navigation_widget)

        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

    def next_step(self) -> None:
        print("Weiter geklickt")