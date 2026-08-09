import os
import json

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
from Hydrology.worker import HydrologyWorker
from resource import resource_path


class BrowserPage(QWidget):

    def __init__(self):
        super().__init__()

        self.dem_files = []
        self.river_file = None
        self.outlet = None
        self.worker = None

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

        toolbar = QVBoxLayout()

        row1 = QHBoxLayout()
        self.btn_dem = QPushButton("Load DEM")
        self.btn_river = QPushButton("Load River")
        row1.addWidget(self.btn_dem)
        row1.addWidget(self.btn_river)

        row2 = QHBoxLayout()
        self.btn_load_outlet = QPushButton("Load Outlet KML")
        self.btn_ws = QPushButton("Watershed")
        row2.addWidget(self.btn_load_outlet)
        row2.addWidget(self.btn_ws)

        toolbar.addLayout(row1)
        toolbar.addLayout(row2)

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

        html = resource_path("web/map.html")
        self.browser.load(QUrl.fromLocalFile(html))

        layout.addWidget(left_widget)
        layout.addWidget(self.browser, 1)

        # Signal Connections
        self.page.coordinateSelected.connect(self.coordinate_received)
        self.btn_dem.clicked.connect(self.load_dem)
        self.btn_river.clicked.connect(self.load_river)
        self.btn_load_outlet.clicked.connect(self.load_outlet_kml)
        self.btn_ws.clicked.connect(self.run_watershed)

    # =====================================================
    # LOAD DEM (DENGAN OTOMATIS TAMPILKAN BOUNDS DI PETA)
    # =====================================================

    def load_dem(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Pilih DEM", "", "GeoTIFF (*.tif *.tiff)"
        )

        if not files:
            return

        existing_names = [os.path.basename(f) for f in self.dem_files]
        new_files = [f for f in files if os.path.basename(f) not in existing_names]
        
        if not new_files:
            QMessageBox.warning(self, "DEM", "File DEM tersebut sudah ada di daftar project.")
            return

        self.dem_files.extend(new_files)

        for f in new_files:
            self.project.add_dem(os.path.basename(f))

        try:
            import rasterio, geopandas as gpd
            from shapely.geometry import box
            
            bounds = [rasterio.open(f).bounds for f in self.dem_files]
            polygon = box(
                min(b.left for b in bounds), min(b.bottom for b in bounds),
                max(b.right for b in bounds), max(b.top for b in bounds)
            )
            
            os.makedirs("output", exist_ok=True)
            bounds_path = os.path.abspath("output/dem_bounds.geojson")
            gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326").to_file(bounds_path, driver="GeoJSON")
            
            with open(bounds_path, "r") as f:
                geojson_data = json.load(f)
            
            script = f"loadDemBounds({json.dumps(geojson_data)});"
            self.page.runJavaScript(script)
        except Exception as e:
            print("Gagal memuat batas DEM ke peta:", e)

        QMessageBox.information(
            self, "DEM", f"{len(new_files)} file DEM baru berhasil ditambahkan."
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
    # LOAD OUTLET KML / KMZ
    # =====================================================

    def load_outlet_kml(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Pilih File KML/KMZ", "", "KML/KMZ (*.kml *.kmz)"
        )

        if not filename:
            return

        try:
            import geopandas as gpd
            gdf = gpd.read_file(filename)
            
            if not gdf.empty:
                point = gdf.geometry.iloc[0]
                lat, lon = point.y, point.x
                
                self.outlet = (lat, lon)
                
                script = f"setOutletMarker({lat}, {lon});"
                self.page.runJavaScript(script)

                QMessageBox.information(
                    self, "Outlet KML", f"Titik outlet berhasil dimuat!\nLat: {lat}, Lon: {lon}"
                )
            else:
                QMessageBox.warning(self, "Outlet KML", "File KML tidak memiliki data geometri.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal membaca file KML: {str(e)}")

    # =====================================================
    # OUTLET KLIK PETA
    # =====================================================

    def coordinate_received(self, lat, lon):
        self.outlet = (lat, lon)

    # =====================================================
    # WATERSHED (MENGGUNAKAN THREAD AGAR BEBAS NOT RESPONDING)
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
                "Silakan klik outlet pada peta atau load KML terlebih dahulu.",
            )
            return

        print("=" * 60)
        print("MENJALANKAN HYDROLOGY ENGINE (BACKGROUND THREAD)")
        print("=" * 60)

        self.btn_ws.setEnabled(False)
        self.btn_ws.setText("Memproses...")

        self.worker = HydrologyWorker(
            dem_files=self.dem_files,
            river_file=self.river_file,
            outlet=self.outlet
        )
        self.worker.progress_signal.connect(self.on_watershed_progress)
        self.worker.finished_signal.connect(self.on_watershed_finished)
        self.worker.error_signal.connect(self.on_watershed_error)
        
        self.worker.start()

    def on_watershed_progress(self, percent, message):
        print(f"[Progress {percent}%]: {message}")

    def on_watershed_finished(self, message, duration, area_km2):
        self.btn_ws.setEnabled(True)
        self.btn_ws.setText("Watershed")

        watershed_geojson_path = os.path.join("output", "watershed.geojson")
        if os.path.exists(watershed_geojson_path):
            with open(watershed_geojson_path, "r") as f:
                geo_content = f.read()
            
            safe_json = json.dumps(json.loads(geo_content))
            script = f"loadWatershed({safe_json});"
            self.page.runJavaScript(script)
        else:
            print("File watershed.geojson tidak ditemukan di folder output!")

        # Menampilkan pesan pop-up lengkap dengan Luas CA dan Waktu Pengerjaan
        info_text = (
            f"{message}\n\n"
            f"📐 Luas Catchment Area (CA) : {area_km2:.3f} km²\n"
            f"⏱️ Waktu pengerjaan          : {duration:.2f} detik"
        )
        QMessageBox.information(self, "Watershed Selesai", info_text)

    def on_watershed_error(self, err_msg):
        self.btn_ws.setEnabled(True)
        self.btn_ws.setText("Watershed")

        QMessageBox.critical(self, "Error Hidrologi", f"Terjadi kesalahan saat proses:\n{err_msg}")