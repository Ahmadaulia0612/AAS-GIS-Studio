from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebChannel import QWebChannel
import json

class MapBridge(QObject):
    coordinateSelected = Signal(float, float)
    @Slot(float, float)
    def receiveOutletCoords(self, lat, lng):
        self.coordinateSelected.emit(lat, lng)

class MapPage(QWebEnginePage):
    coordinateSelected = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bridge = MapBridge()
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self.bridge)
        self.setWebChannel(self.channel)
        self.bridge.coordinateSelected.connect(self.coordinateSelected.emit)

    # Pastikan semua fungsi ini ada agar tidak ada error 'no attribute'
    def loadRiver(self, d): self.runJavaScript(f"loadRiver({json.dumps(d)});")
    def addRiver(self, d): self.runJavaScript(f"addRiver({json.dumps(d)});")
    def loadDemBounds(self, d): self.runJavaScript(f"loadDemBounds({json.dumps(d)});")
    def loadWatershed(self, d): self.runJavaScript(f"loadWatershed({json.dumps(d)});")
    def loadCandidates(self, d): self.runJavaScript(f"loadCandidates({json.dumps(d)});")