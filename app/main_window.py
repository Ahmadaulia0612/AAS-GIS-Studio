from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QIcon

from resource import resource_path
from app.download_page import DownloadPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AAS GIS Studio v1.0")

        self.setWindowIcon(
            QIcon(resource_path("icons/logo.ico"))
        )

        self.resize(900, 700)

        self.setCentralWidget(
            DownloadPage()
        )