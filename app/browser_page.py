import os

from PySide6.QtWidgets import QWidget,QVBoxLayout

from PySide6.QtCore import QUrl

from PySide6.QtWebEngineWidgets import QWebEngineView


class BrowserPage(QWidget):

    def __init__(self):

        super().__init__()

        layout=QVBoxLayout(self)

        self.browser=QWebEngineView()

        layout.addWidget(self.browser)

        html=os.path.abspath(
            "web/map.html"
        )

        self.browser.load(
            QUrl.fromLocalFile(html)
        )