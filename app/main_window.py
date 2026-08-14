from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QMessageBox
)
from PySide6.QtGui import QIcon

from resource import resource_path
from app.download_page import DownloadPage
from app.browser_page import BrowserPage

# Import Worker Thread Hidrologi
from Hydrology.worker import HydrologyWorker

# Import Dialog Unduh Data Iklim (NASA POWER & CHIRPS)
from app.widget.nasa_dialog import ClimateDataDownloadDialog


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AAS GIS Studio v2.0")

        self.setWindowIcon(
            QIcon(resource_path("icons/logo.ico"))
        )

        self.resize(1200, 800)

        tabs = QTabWidget()

        self.download_page = DownloadPage()
        self.browser_page = BrowserPage()

        tabs.addTab(
            self.download_page,
            "Downloader"
        )

        tabs.addTab(
            self.browser_page,
            "Hydrology"
        )

        self.setCentralWidget(tabs)

        # Hubungkan tombol Watershed dan tombol Data Iklim dari halaman Hydrology
        self.connect_signals()

    def connect_signals(self):
        # 1. Hubungkan tombol Watershed
        if hasattr(self.browser_page, "btn_watershed"):
            self.browser_page.btn_watershed.clicked.connect(self.run_watershed_process)

        # 2. Hubungkan tombol Data NASA / Iklim jika ada di browser_page
        # (Jika tombolnya bernama btn_data_nasa atau sejenisnya di halaman Hydrology)
        if hasattr(self.browser_page, "btn_data_nasa"):
            self.browser_page.btn_data_nasa.clicked.connect(self.open_climate_dialog)

    def open_climate_dialog(self):
        # Ambil koordinat aktif dari halaman browser/peta jika tersedia, atau gunakan default
        lat = getattr(self.browser_page, "selected_lat", 0.7265)
        lon = getattr(self.browser_page, "selected_lon", 113.4960)

        # Buka dialog pilihan sumber data (NASA & CHIRPS)
        dialog = ClimateDataDownloadDialog(lat, lon, self)
        dialog.exec()

    def run_watershed_process(self):
        dem_files = getattr(self.browser_page, "dem_files", [])
        river_file = getattr(self.browser_page, "river_file", None)
        outlet = getattr(self.browser_page, "selected_outlet", None)

        if not dem_files or not outlet:
            QMessageBox.warning(self, "Peringatan", "Pastikan DEM dan titik Outlet (peta) sudah dipilih!")
            return

        print("Memulai proses hidrologi di background thread...")

        self.worker = HydrologyWorker(dem_files, river_file, outlet)
        self.worker.progress_signal.connect(self.on_watershed_progress)
        self.worker.finished_signal.connect(self.on_watershed_finished)
        self.worker.error_signal.connect(self.on_watershed_error)
        
        self.worker.start()

    def on_watershed_progress(self, percent, message):
        print(f"[Progress {percent}%]: {message}")
        self.statusBar().showMessage(message, 5000)

    def on_watershed_finished(self, message, duration):
        info_text = f"{message}\n⏱️ Waktu pengerjaan: {duration:.2f} detik"
        QMessageBox.information(self, "Berhasil", info_text)
        self.statusBar().showMessage("Proses Delineasi Selesai", 5000)

    def on_watershed_error(self, err_msg):
        QMessageBox.critical(self, "Error Hidrologi", f"Terjadi kesalahan saat proses:\n{err_msg}")
        self.statusBar().showMessage("Proses Gagal", 5000)