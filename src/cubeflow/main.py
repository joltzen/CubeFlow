import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from cubeflow.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    style_path = (
        Path(__file__).parent
        / "ui"
        / "styles"
        / "main.qss"
    )

    with open(style_path, "r") as style_file:
        app.setStyleSheet(style_file.read())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()