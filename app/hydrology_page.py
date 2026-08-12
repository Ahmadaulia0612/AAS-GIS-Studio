from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
# (Pastikan impor lainnya yang sudah ada di file aslimu tetap dipertahankan)

class HydrologyPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dem_files = []  # List untuk menyimpan path file DEM
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Layout untuk Tombol Load DEM & Hapus DEM
        btn_dem_layout = QHBoxLayout()
        
        self.btn_load_dem = QPushButton("Load DEM")
        self.btn_load_dem.clicked.connect(self.load_dem_files)
        btn_dem_layout.addWidget(self.btn_load_dem)

        # Tombol Hapus DEM yang baru ditambahkan
        self.btn_clear_dem = QPushButton("Hapus DEM")
        self.btn_clear_dem.clicked.connect(self.clear_dem_list)
        btn_dem_layout.addWidget(self.btn_clear_dem)

        main_layout.addLayout(btn_dem_layout)

        # (Lanjutkan dengan kode widget atau layout lain yang sudah ada di file aslimu di bawah sini)

    def load_dem_files(self):
        # Logika pemuatan file DEM yang sudah ada di aplikasimu
        pass

    def clear_dem_list(self):
        """Fungsi untuk membersihkan daftar DEM dan mencegah error merge file korup"""
        self.dem_files = []
        print("INFO: Daftar DEM berhasil dikosongkan.")
        QMessageBox.information(
            self, 
            "DEM Dibersihkan", 
            "Daftar DEM telah dikosongkan. Silakan klik 'Load DEM' kembali untuk memilih file .tif yang valid."
        )