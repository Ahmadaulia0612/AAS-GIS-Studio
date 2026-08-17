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
    QLabel,
    QTreeWidgetItem
)

from app.map_page import MapPage
from app.widget.project_tree import ProjectTree
from Hydrology.engine import HydrologyEngine
from Hydrology.worker import HydrologyWorker
from resource import resource_path


class RiverWorker(QThread):
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

            target_data = (
                river_ln
                if river_ln is not None and not river_ln.empty
                else river_ar
            )

            if target_data is not None and not target_data.empty:
                geojson_str = target_data.to_json()
                self.finished_signal.emit(
                    json.loads(geojson_str)
                )
            else:
                self.error_signal.emit(
                    "File sungai tidak memiliki data geometri yang valid."
                )

        except Exception as e:
            self.error_signal.emit(str(e))


class BrowserPage(QWidget):

    def __init__(self):
        super().__init__()

        self.dem_files = []
        self.river_file = None
        self.outlet = None
        self.calculated_ca_km2 = None

        self.worker = None
        self.river_worker = None

        self.init_ui()

    # ==========================================================
    # UI
    # ==========================================================

    def init_ui(self):

        layout = QHBoxLayout(self)

        # ------------------------------------------------------
        # LEFT PANEL
        # ------------------------------------------------------

        left = QVBoxLayout()

        self.project = ProjectTree()
        left.addWidget(self.project)

        toolbar = QVBoxLayout()

        # ------------------------------------------------------
        # ROW 1
        # ------------------------------------------------------

        row1 = QHBoxLayout()

        self.btn_dem = QPushButton("Load DEM")
        self.btn_river = QPushButton("Load River")

        row1.addWidget(self.btn_dem)
        row1.addWidget(self.btn_river)

        # ------------------------------------------------------
        # ROW 2
        # ------------------------------------------------------

        row2 = QHBoxLayout()

        self.btn_load_outlet = QPushButton(
            "Load Outlet KML"
        )

        self.btn_ws = QPushButton(
            "Watershed"
        )

        row2.addWidget(self.btn_load_outlet)
        row2.addWidget(self.btn_ws)

        # ------------------------------------------------------
        # ROW 3
        # ------------------------------------------------------

        row3 = QHBoxLayout()

        self.btn_export_kml = QPushButton(
            "Export KML"
        )

        self.btn_export_kml.setStyleSheet(
            "background-color: #28a745;"
            "color: white;"
            "font-weight: bold;"
        )

        self.btn_export_kml.setEnabled(False)

        self.btn_calc_energy = QPushButton(
            "Energy"
        )

        self.btn_calc_energy.setStyleSheet(
            "background-color: #17a2b8;"
            "color: white;"
            "font-weight: bold;"
        )

        self.btn_calc_energy.setEnabled(False)

        row3.addWidget(self.btn_export_kml)
        row3.addWidget(self.btn_calc_energy)

        # ------------------------------------------------------
        # ROW 4
        # ------------------------------------------------------

        row4 = QHBoxLayout()

        self.btn_nasa = QPushButton(
            "Data Iklim"
        )

        self.btn_nasa.setStyleSheet(
            "background-color: #ffc107;"
            "color: black;"
            "font-weight: bold;"
        )

        self.btn_nasa.setEnabled(False)

        row4.addWidget(self.btn_nasa)

        # ------------------------------------------------------
        # ADD TOOLBAR
        # ------------------------------------------------------

        toolbar.addLayout(row1)
        toolbar.addLayout(row2)
        toolbar.addLayout(row3)
        toolbar.addLayout(row4)

        left.addLayout(toolbar)

        left_widget = QWidget()
        left_widget.setLayout(left)

        left_widget.setMinimumWidth(320)
        left_widget.setMaximumWidth(360)

        # ------------------------------------------------------
        # MAP
        # ------------------------------------------------------

        self.browser = QWebEngineView()

        self.page = MapPage()

        self.browser.setPage(
            self.page
        )

        settings = self.browser.settings()

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            True
        )

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls,
            True
        )

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled,
            True
        )

        html = resource_path(
            "web/map.html"
        )

        self.browser.load(
            QUrl.fromLocalFile(html)
        )

        # ------------------------------------------------------
        # MAIN LAYOUT
        # ------------------------------------------------------

        layout.addWidget(
            left_widget
        )

        layout.addWidget(
            self.browser,
            1
        )

        # ------------------------------------------------------
        # SIGNALS
        # ------------------------------------------------------

        self.page.coordinateSelected.connect(
            self.coordinate_received
        )

        self.btn_dem.clicked.connect(
            self.load_dem
        )

        self.btn_river.clicked.connect(
            self.load_river
        )

        self.btn_load_outlet.clicked.connect(
            self.load_outlet_kml
        )

        self.btn_ws.clicked.connect(
            self.run_watershed
        )

        self.btn_export_kml.clicked.connect(
            self.export_watershed_kml
        )

        self.btn_calc_energy.clicked.connect(
            self.open_energy_calculator
        )

        self.btn_nasa.clicked.connect(
            self.open_nasa_dialog
        )

    # ==========================================================
    # DEM
    # ==========================================================

    def load_dem(self):

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Pilih DEM",
            "",
            "GeoTIFF (*.tif *.tiff)"
        )

        if not files:
            return

        existing_names = [
            os.path.basename(f)
            for f in self.dem_files
        ]

        new_files = [
            f
            for f in files
            if os.path.basename(f)
            not in existing_names
        ]

        if not new_files:

            QMessageBox.warning(
                self,
                "DEM",
                "File DEM tersebut sudah ada di daftar project."
            )

            return

        self.dem_files.extend(
            new_files
        )

        for f in new_files:

            self.add_dem_item_with_x(
                f,
                os.path.basename(f)
            )

        self.update_dem_bounds_on_map()

        QMessageBox.information(
            self,
            "DEM",
            f"{len(new_files)} file DEM baru berhasil ditambahkan."
        )

    # ==========================================================
    # ADD DEM TREE ITEM
    # ==========================================================

    def add_dem_item_with_x(
        self,
        file_path,
        file_name
    ):

        dem_node = None

        for i in range(
            self.project.topLevelItemCount()
        ):

            top_item = self.project.topLevelItem(i)

            if (
                top_item.text(0)
                .strip()
                .upper()
                == "DEM"
            ):

                dem_node = top_item
                break

            for j in range(
                top_item.childCount()
            ):

                child = top_item.child(j)

                if (
                    child.text(0)
                    .strip()
                    .upper()
                    == "DEM"
                ):

                    dem_node = child
                    break

        target_parent = (
            dem_node
            if dem_node
            else self.project.topLevelItem(0)
        )

        tree_item = QTreeWidgetItem(
            target_parent
        )

        container = QWidget()

        h_layout = QHBoxLayout(
            container
        )

        h_layout.setContentsMargins(
            2, 2, 2, 2
        )

        h_layout.setSpacing(5)

        lbl_name = QLabel(
            file_name
        )

        lbl_name.setStyleSheet(
            "background: transparent;"
        )

        btn_del = QPushButton(
            "✕"
        )

        btn_del.setFixedSize(
            18,
            18
        )

        btn_del.setStyleSheet(
            "background-color: #d9534f;"
            "color: white;"
            "font-weight: bold;"
            "border-radius: 3px;"
            "border: none;"
        )

        btn_del.clicked.connect(
            lambda _,
            fp=file_path,
            it=tree_item:
            self.remove_single_dem(
                fp,
                it
            )
        )

        h_layout.addWidget(
            lbl_name
        )

        h_layout.addStretch()

        h_layout.addWidget(
            btn_del
        )

        self.project.setItemWidget(
            tree_item,
            0,
            container
        )

    # ==========================================================
    # REMOVE DEM
    # ==========================================================

    def remove_single_dem(
        self,
        file_path,
        item
    ):

        if file_path in self.dem_files:

            self.dem_files.remove(
                file_path
            )

        parent = item.parent()

        if parent:

            parent.removeChild(
                item
            )

        self.update_dem_bounds_on_map()

        QMessageBox.information(
            self,
            "DEM Dihapus",
            f"File {os.path.basename(file_path)} berhasil dihapus."
        )

    # ==========================================================
    # DEM BOUNDS
    # ==========================================================

    def update_dem_bounds_on_map(
        self
    ):

        try:

            if not self.dem_files:

                self.page.runJavaScript(
                    "loadDemBounds("
                    "{'type': 'FeatureCollection',"
                    "'features': []}"
                    ");"
                )

                return

            import rasterio
            import geopandas as gpd

            from shapely.geometry import box

            all_bounds = [
                rasterio.open(
                    f
                ).bounds
                for f in self.dem_files
            ]

            minx = min(
                b.left
                for b in all_bounds
            )

            miny = min(
                b.bottom
                for b in all_bounds
            )

            maxx = max(
                b.right
                for b in all_bounds
            )

            maxy = max(
                b.top
                for b in all_bounds
            )

            polygon = box(
                minx,
                miny,
                maxx,
                maxy
            )

            os.makedirs(
                "output",
                exist_ok=True
            )

            bounds_path = os.path.abspath(
                "output/dem_bounds.geojson"
            )

            gpd.GeoDataFrame(
                geometry=[polygon],
                crs="EPSG:4326"
            ).to_file(
                bounds_path,
                driver="GeoJSON"
            )

            with open(
                bounds_path,
                "r",
                encoding="utf-8"
            ) as f:

                geojson_data = json.load(
                    f
                )

            script = (
                f"loadDemBounds("
                f"{json.dumps(geojson_data)}"
                f"); "
                f"fitDemBounds("
                f"[{miny}, {minx}], "
                f"[{maxy}, {maxx}]"
                f");"
            )

            self.page.runJavaScript(
                script
            )

        except Exception as e:

            print(
                "Gagal memperbarui batas DEM ke peta:",
                e
            )

    # ==========================================================
    # RIVER
    # ==========================================================

    def load_river(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih River",
            "",
            "GeoPackage (*.gpkg *.shp)"
        )

        if not filename:
            return

        self.river_file = filename

        self.add_river_item_with_x(
            filename,
            os.path.basename(filename)
        )

        QMessageBox.information(
            self,
            "Memuat River",
            "File sungai sedang dimuat di latar belakang..."
        )

        self.river_worker = RiverWorker(
            filename
        )

        self.river_worker.finished_signal.connect(
            self.on_river_loaded
        )

        self.river_worker.error_signal.connect(
            self.on_river_error
        )

        self.river_worker.start()

    # ==========================================================
    # ADD RIVER TREE ITEM
    # ==========================================================

    def add_river_item_with_x(
        self,
        file_path,
        file_name
    ):

        river_node = None

        for i in range(
            self.project.topLevelItemCount()
        ):

            top_item = self.project.topLevelItem(i)

            if (
                top_item.text(0)
                .strip()
                .upper()
                == "RIVER"
            ):

                river_node = top_item
                break

            for j in range(
                top_item.childCount()
            ):

                child = top_item.child(j)

                if (
                    child.text(0)
                    .strip()
                    .upper()
                    == "RIVER"
                ):

                    river_node = child
                    break

        target_parent = (
            river_node
            if river_node
            else self.project.topLevelItem(0)
        )

        while target_parent.childCount() > 0:

            target_parent.removeChild(
                target_parent.child(0)
            )

        tree_item = QTreeWidgetItem(
            target_parent
        )

        container = QWidget()

        h_layout = QHBoxLayout(
            container
        )

        h_layout.setContentsMargins(
            2, 2, 2, 2
        )

        h_layout.setSpacing(5)

        lbl_name = QLabel(
            file_name
        )

        lbl_name.setStyleSheet(
            "background: transparent;"
        )

        btn_del = QPushButton(
            "✕"
        )

        btn_del.setFixedSize(
            18,
            18
        )

        btn_del.setStyleSheet(
            "background-color: #d9534f;"
            "color: white;"
            "font-weight: bold;"
            "border-radius: 3px;"
            "border: none;"
        )

        btn_del.clicked.connect(
            lambda _,
            fp=file_path,
            it=tree_item:
            self.remove_single_river(
                fp,
                it
            )
        )

        h_layout.addWidget(
            lbl_name
        )

        h_layout.addStretch()

        h_layout.addWidget(
            btn_del
        )

        self.project.setItemWidget(
            tree_item,
            0,
            container
        )

    # ==========================================================
    # REMOVE RIVER
    # ==========================================================

    def remove_single_river(
        self,
        file_path,
        item
    ):

        self.river_file = None

        parent = item.parent()

        if parent:

            parent.removeChild(
                item
            )

        self.page.loadRiver(
            {
                "type": "FeatureCollection",
                "features": []
            }
        )

        QMessageBox.information(
            self,
            "River Dihapus",
            "File sungai berhasil dihapus dari daftar."
        )

    # ==========================================================
    # RIVER LOADED
    # ==========================================================

    def on_river_loaded(
        self,
        geojson_dict
    ):

        if geojson_dict:

            self.page.loadRiver(
                geojson_dict
            )

        QMessageBox.information(
            self,
            "River",
            "Data sungai berhasil ditampilkan di peta!"
        )

    # ==========================================================
    # RIVER ERROR
    # ==========================================================

    def on_river_error(
        self,
        err_msg
    ):

        QMessageBox.critical(
            self,
            "Error River",
            f"Gagal membaca file River:\n{err_msg}"
        )

    # ==========================================================
    # LOAD OUTLET KML
    # ==========================================================

    def load_outlet_kml(
        self
    ):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih File KML/KMZ",
            "",
            "KML/KMZ (*.kml *.kmz)"
        )

        if not filename:
            return

        try:

            import geopandas as gpd

            gdf = gpd.read_file(
                filename
            )

            if not gdf.empty:

                point = gdf.geometry.iloc[0]

                lat = point.y
                lon = point.x

                self.outlet = (
                    lat,
                    lon
                )

                self.btn_nasa.setEnabled(
                    True
                )

                self.page.runJavaScript(
                    f"setOutletMarker("
                    f"{lat}, {lon}"
                    f");"
                )

                QMessageBox.information(
                    self,
                    "Outlet KML",
                    f"Titik outlet dimuat!\n"
                    f"Lat: {lat}\n"
                    f"Lon: {lon}"
                )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                f"Gagal membaca file KML: {str(e)}"
            )

    # ==========================================================
    # MAP COORDINATE
    # ==========================================================

    def coordinate_received(
        self,
        lat,
        lon
    ):

        self.outlet = (
            lat,
            lon
        )

        self.btn_nasa.setEnabled(
            True
        )

        QMessageBox.information(
            self,
            "Outlet Terpilih",
            f"Outlet diatur:\n"
            f"Lat: {lat:.5f}\n"
            f"Lon: {lon:.5f}"
        )

    # ==========================================================
    # EXPORT WATERSHED KML
    # ==========================================================

    def export_watershed_kml(
        self
    ):

        watershed_geojson_path = os.path.join(
            "output",
            "watershed.geojson"
        )

        if not os.path.exists(
            watershed_geojson_path
        ):

            QMessageBox.warning(
                self,
                "Export KML",
                "Belum ada data Watershed."
            )

            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan KML",
            "watershed.kml",
            "KML Files (*.kml)"
        )

        if not filename:
            return

        try:

            import geopandas as gpd

            gdf = gpd.read_file(
                watershed_geojson_path
            )

            if gdf.crs != "EPSG:4326":

                gdf = gdf.to_crs(
                    epsg=4326
                )

            gdf["geometry"] = (
                gdf["geometry"].simplify(
                    tolerance=0.0008,
                    preserve_topology=True
                )
            )

            gdf.to_file(
                filename,
                driver="KML"
            )

            QMessageBox.information(
                self,
                "Export KML Berhasil",
                f"Disimpan di:\n{filename}"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error Export",
                f"Gagal:\n{str(e)}"
            )

    # ==========================================================
    # ENERGY
    # ==========================================================

    def open_energy_calculator(
        self
    ):

        from app.widget.energy_dialog import (
            EnergyCalculatorDialog
        )

        dialog = EnergyCalculatorDialog(
            self
        )

        dialog.exec()

    # ==========================================================
    # NASA / CLIMATE
    # ==========================================================

    def open_nasa_dialog(
        self
    ):

        if self.outlet is None:

            QMessageBox.warning(
                self,
                "Peringatan",
                "Silakan tentukan titik outlet terlebih dahulu pada peta."
            )

            return

        from app.widget.nasa_dialog import (
            ClimateDataDownloadDialog
        )

        lat, lon = self.outlet

        dialog = ClimateDataDownloadDialog(
            lat,
            lon,
            self
        )

        dialog.exec()

    # ==========================================================
    # RUN WATERSHED
    # ==========================================================

    def run_watershed(
        self
    ):

        if (
            not self.dem_files
            or not self.river_file
            or self.outlet is None
        ):

            QMessageBox.warning(
                self,
                "Hydrology",
                "Pastikan DEM, River, dan Outlet sudah dipilih."
            )

            return

        self.btn_ws.setEnabled(
            False
        )

        self.btn_ws.setText(
            "Memproses..."
        )

        self.worker = HydrologyWorker(
            dem_files=self.dem_files,
            river_file=self.river_file,
            outlet=self.outlet
        )

        self.worker.progress_signal.connect(
            lambda p, m:
            print(
                f"[{p}%]: {m}"
            )
        )

        self.worker.finished_signal.connect(
            self.on_watershed_finished
        )

        self.worker.error_signal.connect(
            self.on_watershed_error
        )

        self.worker.start()

    # ==========================================================
    # WATERSHED FINISHED
    # ==========================================================

    def on_watershed_finished(
        self,
        message,
        duration,
        area_km2
    ):

        self.btn_ws.setEnabled(
            True
        )

        self.btn_ws.setText(
            "Watershed"
        )

        self.calculated_ca_km2 = (
            area_km2
        )

        self.btn_export_kml.setEnabled(
            True
        )

        self.btn_calc_energy.setEnabled(
            True
        )

        # ------------------------------------------------------
        # UPDATE PROJECT TREE
        # ------------------------------------------------------

        self.project.set_watershed_info(
            area_km2=area_km2,
            outlet=self.outlet,
            duration=duration,
            status="READY"
        )

        # ------------------------------------------------------
        # LOAD WATERSHED KE PETA
        # ------------------------------------------------------

        watershed_geojson_path = os.path.join(
            "output",
            "watershed.geojson"
        )

        if os.path.exists(
            watershed_geojson_path
        ):

            with open(
                watershed_geojson_path,
                "r",
                encoding="utf-8"
            ) as f:

                geo_content = f.read()

            self.page.runJavaScript(
                f"loadWatershed("
                f"{json.dumps(json.loads(geo_content))}"
                f");"
            )

        # ------------------------------------------------------
        # POPUP HASIL
        # ------------------------------------------------------

        QMessageBox.information(
            self,
            "Selesai",
            f"{message}\n\n"
            f"Luas CA: {area_km2:.3f} km²\n"
            f"Waktu: {duration:.2f} detik"
        )

    # ==========================================================
    # WATERSHED ERROR
    # ==========================================================

    def on_watershed_error(
        self,
        err_msg
    ):

        self.btn_ws.setEnabled(
            True
        )

        self.btn_ws.setText(
            "Watershed"
        )

        QMessageBox.critical(
            self,
            "Error",
            f"Terjadi kesalahan:\n{err_msg}"
        )