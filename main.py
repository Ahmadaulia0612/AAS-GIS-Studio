import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from resource import resource_path
from app.main_window import MainWindow


def main():

    app = QApplication(sys.argv)

    app.setWindowIcon(
        QIcon(resource_path("icons/logo.ico"))
    )

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()