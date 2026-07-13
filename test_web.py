from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView

app = QApplication([])

view = QWebEngineView()
view.load("https://www.google.com")
view.show()

app.exec()