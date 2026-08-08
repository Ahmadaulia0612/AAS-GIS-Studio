from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget
)

from PySide6.QtGui import QIcon

from resource import resource_path

from app.download_page import DownloadPage
from app.browser_page import BrowserPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AAS GIS Studio v2.0")

        self.setWindowIcon(
            QIcon(resource_path("icons/logo.ico"))
        )

        self.resize(1200, 800)

        tabs = QTabWidget()

        tabs.addTab(
            DownloadPage(),
            "Downloader"
        )

        tabs.addTab(
            BrowserPage(),
            "Hydrology"
        )

        self.setCentralWidget(tabs)