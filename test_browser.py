from PySide6.QtWidgets import QApplication

from app.browser_page import BrowserPage

app = QApplication([])

w = BrowserPage()

w.resize(1400,900)

w.show()

app.exec()