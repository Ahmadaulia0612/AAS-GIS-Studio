import os

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.map_page import MapPage
from app.widget.project_tree import ProjectTree
from Hydrology.engine import HydrologyEngine
from resource import resource_path


class BrowserPage(QWidget):

    def __init__(self):
        super().__init__()

        self.dem_files = []
        self.river_file = None
        self.outlet = None

        self.init_ui()

    # =====================================================
    # UI
    # =====================================================

    def init_ui(self):
        layout = QHBoxLayout(self)

        # -----------------------------
        # PANEL KIRI
        # -----------------------------
        left = QVBoxLayout()

        self.project = ProjectTree()
        left.addWidget(self.project)

        toolbar = QHBoxLayout()

        self.btn_dem = QPushButton("Load DEM")
        self.btn_river = QPushButton("Load River")
        self.btn_ws = QPushButton("Watershed")

        toolbar.addWidget(self.btn_dem)
        toolbar.addWidget(self.btn_river)
        toolbar.addWidget(self.btn_ws)

        left.addLayout(toolbar)

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setMinimumWidth(320)
        left_widget.setMaximumWidth(360)

        # -----------------------------
        # MAP
        # -----------------------------
        self.browser = QWebEngineView()

        self.page = MapPage()
        self.browser.setPage(self.page)

        settings = self.browser.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            True,
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls,
            True,
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled,
            True,
        )

        html = resource_path("modules/web/map.html")
        self.browser.load(QUrl.fromLocalFile(html))

        layout.addWidget(left_widget)
        layout.addWidget(self.browser, 1)

        # Signal Connections
        self.page.coordinateSelected.connect(self.coordinate_received)
        self.btn_dem.clicked.connect(self.load_dem)
        self.btn_river.clicked.connect(self.load_river)
        self.btn_ws.clicked.connect(self.run_watershed)

    # =====================================================
    # LOAD DEM
    # =====================================================

    def load_dem(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Pilih DEM", "", "GeoTIFF (*.tif *.tiff)"
        )

        if not files:
            return

        self.dem_files = files

        for f in files:
            self.project.add_dem(os.path.basename(f))

        QMessageBox.information(
            self, "DEM", f"{len(files)} file DEM berhasil dipilih."
        )

    # =====================================================
    # LOAD RIVER
    # =====================================================

    def load_river(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Pilih River", "", "GeoPackage (*.gpkg *.shp)"
        )

        if not filename:
            return

        self.river_file = filename

        self.project.add_river(os.path.basename(filename))

        try:
            from Hydrology.river.reader import RiverReader
            
            reader = RiverReader()
            river_ln, river_ar = reader.load(filename)
            
            if river_ln is not None:
                self.page.loadRiver(river_ln.to_json())
                
            if river_ar is not None:
                self.page.addRiver(river_ar.to_json())

            QMessageBox.information(
                self, "River", "River berhasil ditampilkan."
            )

        except Exception as e:
            QMessageBox.critical(self, "River", str(e))

    # =====================================================
    # OUTLET
    # =====================================================

    def coordinate_received(self, lat, lon):
        self.outlet = (lat, lon)

        print("=" * 60)
        print("OUTLET")
        print("Latitude :", lat)
        print("Longitude:", lon)
        print("=" * 60)

    # =====================================================
    # WATERSHED
    # =====================================================

    def run_watershed(self):
        if not self.dem_files:
            QMessageBox.warning(
                self, "Hydrology", "Silakan pilih DEM terlebih dahulu."
            )
            return

        if not self.river_file:
            QMessageBox.warning(
                self, "Hydrology", "Silakan pilih River terlebih dahulu."
            )
            return

        if self.outlet is None:
            QMessageBox.warning(
                self,
                "Hydrology",
                "Silakan klik outlet pada peta terlebih dahulu.",
            )
            return

        print("=" * 60)
        print("RUN WATERSHED")
        print("=" * 60)

        print("Jumlah DEM :", len(self.dem_files))

        for f in self.dem_files:
            print(f)

        print("River :", self.river_file)
        print("Outlet :", self.outlet)

        engine = HydrologyEngine(
            dem_files=self.dem_files,
            river_file=self.river_file,
            outlet=self.outlet,
        )

        engine.run()