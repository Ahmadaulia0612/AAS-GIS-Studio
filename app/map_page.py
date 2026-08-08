from PySide6.QtCore import QObject, Signal, Slot, QUrl
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebChannel import QWebChannel
from resource import resource_path

class MapBridge(QObject):
    coordinateSelected = Signal(float, float)

    @Slot(float, float)
    def receiveOutletCoords(self, lat, lng):
        print(f"Bridge menerima koordinat: {lat}, {lng}")
        self.coordinateSelected.emit(lat, lng)

class MapPage(QWebEnginePage):
    coordinateSelected = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup Jembatan komunikasi
        self.bridge = MapBridge()
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self.bridge)
        self.setWebChannel(self.channel)

        # Sambungkan signal
        self.bridge.coordinateSelected.connect(self.coordinateSelected.emit)

    def loadRiver(self, geojsonStr):
        # Menggunakan format string JSON yang aman
        import json
        safe_json = json.dumps(geojsonStr)
        self.runJavaScript(f"loadRiver({safe_json});")

    def addRiver(self, geojsonStr):
        import json
        safe_json = json.dumps(geojsonStr)
        self.runJavaScript(f"addRiver({safe_json});")