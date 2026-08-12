import os
import json

from PySide6.QtCore import QUrl, QThread, Signal
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QLabel,
    QTreeWidgetItem
)

from app.map_page import MapPage
from app.widget.project_tree import ProjectTree
from Hydrology.engine import HydrologyEngine
from Hydrology.worker import HydrologyWorker
from Hydrology.scanner import RiverScanner
from resource import resource_path


class RiverWorker(QThread):
    """Worker thread untuk memuat file sungai besar tanpa membuat GUI freeze"""
    finished_signal = Signal(object)
    error_signal = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            from Hydrology.river.reader import RiverReader
            reader = RiverReader()
            river_ln, river_ar = reader.load(self.path)
            
            target_data = river_ln if river_ln is not None and not river_ln.empty else river_ar
            
            if target_data is not None and not target_data.empty:
                geojson_str = target_data.to_json()
                self.finished_signal.emit(json.loads(geojson_str))
            else:
                self.error_signal.emit("File sungai tidak memiliki data geometri yang valid.")
        except Exception as e:
            self.error_signal.emit(str(e))


class BrowserPage(QWidget):

    def __init__(self):
        super().__init__()

        self.dem_files = []
        self.river_file = None
        self.outlet = None
        self.worker = None
        self.river_worker = None

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

        # --- TOMBOL EXPORT KML ---
        row_export = QHBoxLayout()
        self.btn_export_kml = QPushButton("📥 Export KML")
        self.btn_export_kml.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        self.btn_export_kml.setEnabled(False)  # Dikunci secara default saat aplikasi dibuka
        row_export.addWidget(self.btn_export_kml)
        # -------------------------

        # --- INPUT & TOMBOL HYDROPOWER SCANNING ---
        row_scan_input = QHBoxLayout()
        row_scan_input.addWidget(QLabel("Target MW:"))
        self.input_target_mw = QLineEdit("1.0")
        row_scan_input.addWidget(self.input_target_mw)

        self.btn_scan = QPushButton("⚡ Scan Hydropower")
        self.btn_scan.setStyleSheet("background-color: #ff7800; color: white; font-weight: bold;")
        # ------------------------------------------

        toolbar.addLayout(row1)
        toolbar.addLayout(row2)
        toolbar.addLayout(row_export)
        toolbar.addLayout(row_scan_input)
        toolbar.addWidget(self.btn_scan)

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
        self.btn_export_kml.clicked.connect(self.export_watershed_kml)
        self.btn_scan.clicked.connect(self.run_hydropower_scan)

    # =====================================================
    # LOAD DEM & DELETE SINGLE DEM
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
            file_name = os.path.basename(f)
            self.add_dem_item_with_x(f, file_name)

        self.update_dem_bounds_on_map()

        QMessageBox.information(
            self, "DEM", f"{len(new_files)} file DEM baru berhasil ditambahkan."
        )

    def add_dem_item_with_x(self, file_path, file_name):
        dem_node = None
        
        for i in range(self.project.topLevelItemCount()):
            top_item = self.project.topLevelItem(i)
            if top_item.text(0).strip().upper() == "DEM":
                dem_node = top_item
                break
            for j in range(top_item.childCount()):
                child = top_item.child(j)
                if child.text(0).strip().upper() == "DEM":
                    dem_node = child
                    break

        target_parent = dem_node if dem_node else self.project.topLevelItem(0)
        tree_item = QTreeWidgetItem(target_parent)

        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(2, 2, 2, 2)
        h_layout.setSpacing(5)

        lbl_name = QLabel(file_name)
        lbl_name.setStyleSheet("background: transparent;")

        btn_del = QPushButton("✕")
        btn_del.setFixedSize(18, 18)
        btn_del.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold; border-radius: 3px; border: none;")
        btn_del.clicked.connect(lambda _, fp=file_path, it=tree_item: self.remove_single_dem(fp, it))

        h_layout.addWidget(lbl_name)
        h_layout.addStretch()
        h_layout.addWidget(btn_del)

        self.project.setItemWidget(tree_item, 0, container)

    def remove_single_dem(self, file_path, item):
        if file_path in self.dem_files:
            self.dem_files.remove(file_path)

        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            index = self.project.indexOfTopLevelItem(item)
            if index >= 0:
                self.project.takeTopLevelItem(index)

        self.update_dem_bounds_on_map()
        QMessageBox.information(self, "DEM Dihapus", f"File {os.path.basename(file_path)} berhasil dihapus dari daftar.")

    def update_dem_bounds_on_map(self):
        try:
            if not self.dem_files:
                self.page.runJavaScript("loadDemBounds({'type': 'FeatureCollection', 'features': []});")
                return

            import rasterio, geopandas as gpd
            from shapely.geometry import box
            
            all_bounds = [rasterio.open(f).bounds for f in self.dem_files]
            
            minx = min(b.left for b in all_bounds)
            miny = min(b.bottom for b in all_bounds)
            maxx = max(b.right for b in all_bounds)
            maxy = max(b.top for b in all_bounds)
            
            polygon = box(minx, miny, maxx, maxy)
            
            os.makedirs("output", exist_ok=True)
            bounds_path = os.path.abspath("output/dem_bounds.geojson")
            gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326").to_file(bounds_path, driver="GeoJSON")
            
            with open(bounds_path, "r") as f:
                geojson_data = json.load(f)
            
            script = f"loadDemBounds({json.dumps(geojson_data)}); fitDemBounds([{miny}, {minx}], [{maxy}, {maxx}]);"
            self.page.runJavaScript(script)
        except Exception as e:
            print("Gagal memperbarui batas DEM ke peta:", e)

    # =====================================================
    # LOAD RIVER (DENGAN BACKGROUND WORKER)
    # =====================================================

    def load_river(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Pilih River", "", "GeoPackage (*.gpkg *.shp)"
        )

        if not filename:
            return

        self.river_file = filename
        self.project.add_river(os.path.basename(filename))

        QMessageBox.information(self, "Memuat River", "File sungai sedang dimuat di latar belakang. Mohon tunggu sebentar...")

        self.river_worker = RiverWorker(filename)
        self.river_worker.finished_signal.connect(self.on_river_loaded)
        self.river_worker.error_signal.connect(self.on_river_error)
        self.river_worker.start()

    def on_river_loaded(self, geojson_dict):
        if geojson_dict:
            self.page.loadRiver(geojson_dict)
        QMessageBox.information(self, "River", "Data sungai berhasil ditampilkan secara utuh di peta!")

    def on_river_error(self, err_msg):
        QMessageBox.critical(self, "Error River", f"Gagal membaca file River:\n{err_msg}")

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
        QMessageBox.information(self, "Outlet Terpilih", f"Outlet berhasil diatur:\nLat: {lat:.5f}\nLon: {lon:.5f}")

    # =====================================================
    # EXPORT WATERSHED TO KML
    # =====================================================

    def export_watershed_kml(self):
        watershed_geojson_path = os.path.join("output", "watershed.geojson")
        if not os.path.exists(watershed_geojson_path):
            QMessageBox.warning(self, "Export KML", "Belum ada data Watershed yang terbentuk. Silakan jalankan Watershed terlebih dahulu.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Simpan Watershed sebagai KML", "watershed.kml", "KML Files (*.kml)"
        )

        if not filename:
            return

        try:
            import geopandas as gpd
            gdf = gpd.read_file(watershed_geojson_path)
            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)
            
            gdf.to_file(filename, driver='KML')
            QMessageBox.information(self, "Export KML Berhasil", f"File KML berhasil disimpan di:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error Export KML", f"Gagal menyimpan file KML:\n{str(e)}")

    # =====================================================
    # HYDROPOWER SCANNING & CLUSTERING
    # =====================================================

    def run_hydropower_scan(self):
        if not self.dem_files:
            QMessageBox.warning(self, "Hydropower Scan", "Silakan pilih file DEM terlebih dahulu.")
            return

        if not self.river_file:
            QMessageBox.warning(self, "Hydropower Scan", "Silakan pilih file River terlebih dahulu.")
            return

        try:
            target_mw = float(self.input_target_mw.text())
        except ValueError:
            QMessageBox.warning(self, "Hydropower Scan", "Target MW harus berupa angka (contoh: 1.0).")
            return

        dem_file_path = self.dem_files[0]
        flow_acc_path = "output/flow_acc.tif"

        if not os.path.exists(flow_acc_path):
            QMessageBox.warning(self, "Hydropower Scan", "File Flow Accumulation belum ditemukan. Jalankan Watershed terlebih dahulu.")
            return

        self.btn_scan.setEnabled(False)
        self.btn_scan.setText("Memindai...")

        try:
            scanner = RiverScanner(
                river_path=self.river_file,
                dem_path=dem_file_path,
                flow_acc_path=flow_acc_path,
                penstock_length_m=1500
            )

            candidates = scanner.scan(target_mw=target_mw)

            from Hydrology.exporter import export_candidates_to_geojson
            export_candidates_to_geojson(candidates, "output/candidates.geojson")

            with open("output/candidates.geojson", "r", encoding="utf-8") as f:
                geo_data = json.load(f)
            self.page.loadCandidates(geo_data)

            QMessageBox.information(
                self, 
                "Scanning Selesai", 
                f"Berhasil menemukan {len(candidates)} titik potensial setelah proses klasterisasi!"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error Scan", f"Terjadi kesalahan saat pemindaian:\n{str(e)}")
        
        self.btn_scan.setEnabled(True)
        self.btn_scan.setText("⚡ Scan Hydropower")

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
                "Silakan klik outlet pada peta atau load KML terlebih dahulu.",
            )
            return

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
        
        # AKTIFKAN TOMBOL EXPORT KML SETELAH PROSES SELESAI
        self.btn_export_kml.setEnabled(True)

        watershed_geojson_path = os.path.join("output", "watershed.geojson")
        if os.path.exists(watershed_geojson_path):
            with open(watershed_geojson_path, "r") as f:
                geo_content = f.read()
            
            safe_json = json.dumps(json.loads(geo_content))
            script = f"loadWatershed({safe_json});"
            self.page.runJavaScript(script)

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