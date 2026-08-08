from urllib.parse import parse_qs

from PySide6.QtCore import Signal
from PySide6.QtWebEngineCore import QWebEnginePage


class MapPage(QWebEnginePage):

    coordinateSelected = Signal(float, float)

    def __init__(self, parent=None):

        super().__init__(parent)

    # =======================================================
    # Python -> JavaScript
    # =======================================================

    def loadRiver(self, geojson: str):

        geojson = (
            geojson
            .replace("\\", "\\\\")
            .replace("`", "\\`")
        )

        self.runJavaScript(
            f"""
            loadRiver(`{geojson}`);
            """
        )

    def addRiver(self, geojson: str):

        geojson = (
            geojson
            .replace("\\", "\\\\")
            .replace("`", "\\`")
        )

        self.runJavaScript(
            f"""
            addRiver(`{geojson}`);
            """
        )

    def loadWatershed(self, geojson: str):

        geojson = (
            geojson
            .replace("\\", "\\\\")
            .replace("`", "\\`")
        )

        self.runJavaScript(
            f"""
            loadWatershed(`{geojson}`);
            """
        )

    # =======================================================
    # JavaScript -> Python
    # =======================================================

    def acceptNavigationRequest(
        self,
        url,
        nav_type,
        isMainFrame
    ):

        if url.scheme() == "aas":

            try:

                params = parse_qs(url.query())

                lat = float(params["lat"][0])
                lon = float(params["lon"][0])

                print("=" * 40)
                print("Outlet Selected")
                print(lat)
                print(lon)
                print("=" * 40)

                self.coordinateSelected.emit(
                    lat,
                    lon
                )

            except Exception as e:

                print(e)

            return False

        return super().acceptNavigationRequest(
            url,
            nav_type,
            isMainFrame
        )