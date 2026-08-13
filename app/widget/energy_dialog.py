import os
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QGroupBox, QFormLayout, QWidget
)

class EnergyCalculatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Kalkulator Potensi Energi & Hydropower")
        self.setMinimumWidth(450)

        # Terapkan stylesheet global agar teks pada QLineEdit selalu jelas (warna putih/terang)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
                border-radius: 3px;
            }
            QLineEdit:read-only {
                background-color: #1e1e1e;
                color: #00ffcc;
            }
        """)

        self.init_ui()
        self.load_watershed_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        group_info = QGroupBox("Parameter Perhitungan PLTA/PLTM (Standar Excel)")
        form_info = QFormLayout(group_info)
        
        # Input Catchment Area (CA)
        self.input_ca = QLineEdit("0.0")
        self.input_ca.textChanged.connect(self.auto_calculate_q)
        form_info.addRow("Luas Catchment Area (CA) [km²]:", self.input_ca)

        self.input_head = QLineEdit("74.0")
        form_info.addRow("Gross Head (H) [m]:", self.input_head)

        # Input Percentage CA (%) standar Excel (default 9.0%)
        self.input_pct_ca = QLineEdit("9.0")
        self.input_pct_ca.textChanged.connect(self.auto_calculate_q)
        form_info.addRow("Percentage CA (%):", self.input_pct_ca)

        # Design Flow (Q) otomatis terhitung
        self.input_q = QLineEdit("0.0")
        self.input_q.setReadOnly(True)
        form_info.addRow("Design Flow (Q) [m³/s]:", self.input_q)

        # Capacity Factor (CF %) diketik manual
        cf_container = QWidget()
        cf_vbox = QVBoxLayout(cf_container)
        cf_vbox.setContentsMargins(0, 0, 0, 0)
        self.input_cf = QLineEdit("40.0")
        self.lbl_cf_hint = QLabel("💡 Standar: 6% (Mikro), 10% (Peaker), 40% (RoR), 60% (Base Load)")
        self.lbl_cf_hint.setStyleSheet("color: #adb5bd; font-size: 11px;")
        cf_vbox.addWidget(self.input_cf)
        cf_vbox.addWidget(self.lbl_cf_hint)
        
        form_info.addRow("Capacity Factor (CF %):", cf_container)

        layout.addWidget(group_info)

        # Tombol Hitung
        self.btn_calculate = QPushButton("Hitung Potensi Energi")
        self.btn_calculate.setStyleSheet("background-color: #007acc; color: white; font-weight: bold; padding: 8px;")
        self.btn_calculate.clicked.connect(self.calculate_energy)
        layout.addWidget(self.btn_calculate)

        # Hasil Perhitungan
        group_result = QGroupBox("Hasil Estimasi Potensi (Standar PLN/Excel)")
        form_result = QFormLayout(group_result)

        self.lbl_mw = QLabel("- MW")
        self.lbl_gwh = QLabel("- GWh/tahun")

        self.lbl_mw.setStyleSheet("font-weight: bold; color: #28a745; font-size: 14px;")
        self.lbl_gwh.setStyleSheet("font-weight: bold; color: #ff7800; font-size: 14px;")

        form_result.addRow("Kapasitas Terpasang (P):", self.lbl_mw)
        form_result.addRow("Energi Tahunan (E):", self.lbl_gwh)

        layout.addWidget(group_result)

        # Tombol Tutup
        self.btn_close = QPushButton("Tutup")
        self.btn_close.clicked.connect(self.accept)
        layout.addWidget(self.btn_close)

    def load_watershed_data(self):
        watershed_path = os.path.join("output", "watershed.geojson")
        if os.path.exists(watershed_path):
            try:
                import geopandas as gpd
                gdf = gpd.read_file(watershed_path)
                if not gdf.empty:
                    gdf_m = gdf.to_crs(epsg=3857)
                    area_m2 = gdf_m.geometry.area.sum()
                    ca_km2 = area_m2 / 1_000_000.0
                    self.input_ca.setText(f"{ca_km2:.3f}")
                    return
            except Exception as e:
                print("Gagal membaca area watershed untuk kalkulator:", e)
        
        self.input_ca.setText("865.409")

    def auto_calculate_q(self):
        try:
            ca = float(self.input_ca.text())
            pct = float(self.input_pct_ca.text()) / 100.0
            q_val = ca * pct
            self.input_q.setText(f"{q_val:.3f}")
        except ValueError:
            self.input_q.setText("0.0")

    def calculate_energy(self):
        try:
            ca = float(self.input_ca.text())
            head = float(self.input_head.text())
            q_val = float(self.input_q.text())
            cf_val = float(self.input_cf.text()) / 100.0

            if ca <= 0:
                QMessageBox.warning(self, "Peringatan", "Luas Catchment Area harus lebih besar dari 0.")
                return

            # Rumus Baku Excel:
            # 1. Installed Capacity (MW) = 0.008 * Q * H
            installed_capacity_mw = 0.008 * q_val * head

            # 2. Annual Energy (GWh) = Capacity * CF * 8.76
            annual_energy_gwh = installed_capacity_mw * cf_val * 8.76

            self.lbl_mw.setText(f"{installed_capacity_mw:.3f} MW")
            self.lbl_gwh.setText(f"{annual_energy_gwh:.3f} GWh/tahun")

        except ValueError:
            QMessageBox.warning(self, "Error Input", "Pastikan semua kolom angka terisi dengan format yang valid.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))