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

        # Hubungkan tombol Watershed dari halaman Hydrology ke fungsi Thread
        self.connect_signals()

    def connect_signals(self):
        # Asumsikan browser_page memiliki tombol atau event untuk menjalankan watershed
        # Sesuaikan dengan nama tombol di halaman browser/hydrology-mu jika ada
        if hasattr(self.browser_page, "btn_watershed"):
            self.browser_page.btn_watershed.clicked.connect(self.run_watershed_process)

    def run_watershed_process(self):
        # Ambil data DEM, River, dan Outlet dari halaman terkait
        # Sesuaikan variabel ini dengan struktur atribut di aplikasi aslimu
        dem_files = getattr(self.browser_page, "dem_files", [])
        river_file = getattr(self.browser_page, "river_file", None)
        outlet = getattr(self.browser_page, "selected_outlet", None)

        if not dem_files or not outlet:
            QMessageBox.warning(self, "Peringatan", "Pastikan DEM dan titik Outlet (peta) sudah dipilih!")
            return

        print("Memulai proses hidrologi di background thread...")

        # Jalankan worker thread agar aplikasi tidak Not Responding / Freeze
        self.worker = HydrologyWorker(dem_files, river_file, outlet)
        self.worker.progress_signal.connect(self.on_watershed_progress)
        self.worker.finished_signal.connect(self.on_watershed_finished)
        self.worker.error_signal.connect(self.on_watershed_error)
        
        self.worker.start()

    def on_watershed_progress(self, percent, message):
        print(f"[Progress {percent}%]: {message}")
        # Jika kamu ingin menampilkan teks di status bar jendela utama:
        self.statusBar().showMessage(message, 5000)

    def on_watershed_finished(self, message, duration):
        info_text = f"{message}\n⏱️ Waktu pengerjaan: {duration:.2f} detik"
        QMessageBox.information(self, "Berhasil", info_text)
        self.statusBar().showMessage("Proses Delineasi Selesai", 5000)

    def on_watershed_error(self, err_msg):
        QMessageBox.critical(self, "Error Hidrologi", f"Terjadi kesalahan saat proses:\n{err_msg}")
        self.statusBar().showMessage("Proses Gagal", 5000)