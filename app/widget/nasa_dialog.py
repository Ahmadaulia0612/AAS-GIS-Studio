import requests
import json
from datetime import datetime, timedelta
from PySide6.QtCore import QThread, Signal, QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QDateEdit, QComboBox, QPushButton, QMessageBox, QProgressBar
)

class NasaWorker(QThread):
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, lat, lon, start_date, end_date, temporal):
        super().__init__()
        self.lat = lat
        self.lon = lon
        self.start_date = start_date
        self.end_date = end_date
        self.temporal = temporal

    def run(self):
        try:
            url = (
                f"https://power.larc.nasa.gov/api/temporal/{self.temporal}/point?"
                f"parameters=PRECTOTCORR&community=RE&longitude={self.lon}&latitude={self.lat}"
                f"&start={self.start_date}&end={self.end_date}&format=JSON"
            )
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.finished_signal.emit(data)
            else:
                self.error_signal.emit(f"Gagal dari NASA (Status Code: {response.status_code}).\nKemungkinan data untuk rentang tanggal tersebut belum tersedia.")
        except Exception as e:
            self.error_signal.emit(f"Terjadi kesalahan koneksi: {str(e)}")


class NasaDownloadDialog(QDialog):
    def __init__(self, lat, lon, parent=None):
        super().__init__(parent)
        self.lat = lat
        self.lon = lon
        self.worker = None

        self.setWindowTitle("Unduh Data Curah Hujan NASA POWER")
        self.setFixedSize(380, 260)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        lbl_info = QLabel(f"Koordinat Target:\nLatitude: {self.lat:.4f}, Longitude: {self.lon:.4f}")
        lbl_info.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(lbl_info)

        layout.addWidget(QLabel("Pilih Resolusi Waktu:"))
        self.combo_temporal = QComboBox()
        self.combo_temporal.addItems(["Harian (Daily)", "Bulanan (Monthly)", "Tahunan (Annual)"])
        layout.addWidget(self.combo_temporal)

        date_layout = QHBoxLayout()
        
        today = QDate.currentDate()
        default_end = today.addDays(-5)
        default_start = default_end.addYears(-3)

        start_v = QVBoxLayout()
        start_v.addWidget(QLabel("Tanggal Mulai:"))
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(default_start)
        start_v.addWidget(self.date_start)
        date_layout.addLayout(start_v)

        end_v = QVBoxLayout()
        end_v.addWidget(QLabel("Tanggal Selesai:"))
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(default_end)
        end_v.addWidget(self.date_end)
        date_layout.addLayout(end_v)

        layout.addLayout(date_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.btn_download = QPushButton("📥 Unduh Data NASA (.xlsx)")
        self.btn_download.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px;")
        self.btn_download.clicked.connect(self.start_download)
        layout.addWidget(self.btn_download)

    def start_download(self):
        idx = self.combo_temporal.currentIndex()
        temporal_map = ["daily", "monthly", "annual"]
        temporal = temporal_map[idx]

        start_str = self.date_start.date().toString("yyyyMMdd")
        end_str = self.date_end.date().toString("yyyyMMdd")

        if start_str >= end_str:
            QMessageBox.warning(self, "Peringatan", "Tanggal mulai harus lebih awal dari tanggal selesai.")
            return

        self.btn_download.setEnabled(False)
        self.progress_bar.show()

        self.worker = NasaWorker(self.lat, self.lon, start_str, end_str, temporal)
        self.worker.finished_signal.connect(self.on_download_finished)
        self.worker.error_signal.connect(self.on_download_error)
        self.worker.start()

    def on_download_finished(self, data):
        self.btn_download.setEnabled(True)
        self.progress_bar.hide()
        
        try:
            parameters = data.get("properties", {}).get("parameter", {}).get("PRECTOTCORR", {})
            if not parameters:
                QMessageBox.warning(self, "Data Kosong", "Tidak ada data curah hujan yang ditemukan.")
                return

            import os
            import pandas as pd
            
            df = pd.DataFrame(list(parameters.items()), columns=["Tanggal", "Curah_Hujan_mm"])
            df['Tanggal'] = pd.to_datetime(df['Tanggal'], format='%Y%m%d')
            df['Tahun'] = df['Tanggal'].dt.year
            df['Bulan'] = df['Tanggal'].dt.month
            
            monthly_avg = df.groupby(['Tahun', 'Bulan'])['Curah_Hujan_mm'].mean().unstack(level=1).round(2)
            monthly_avg.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
            
            os.makedirs("output", exist_ok=True)
            output_path = os.path.abspath("output/nasa_rainfall_matrix.xlsx")
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                monthly_avg.to_excel(writer, sheet_name='Matriks Hujan')
                
                workbook = writer.book
                worksheet = writer.sheets['Matriks Hujan']
                
                max_row = len(monthly_avg) + 1
                
                worksheet.cell(row=max_row + 1, column=1, value='Min')
                worksheet.cell(row=max_row + 2, column=1, value='Max')
                worksheet.cell(row=max_row + 3, column=1, value='Rata2')
                
                for col_idx in range(2, 14):
                    col_letter = worksheet.cell(row=1, column=col_idx).coordinate[0]
                    worksheet.cell(row=max_row + 1, column=col_idx, value=f'=MIN({col_letter}2:{col_letter}{max_row})')
                    worksheet.cell(row=max_row + 2, column=col_idx, value=f'=MAX({col_letter}2:{col_letter}{max_row})')
                    worksheet.cell(row=max_row + 3, column=col_idx, value=f'=AVERAGE({col_letter}2:{col_letter}{max_row})')

            QMessageBox.information(
                self, "Berhasil", 
                f"Data NASA berhasil disimpan berformat Excel (.xlsx) dengan rumus formula asli!\nDisimpan di:\n{output_path}"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error Parsing", f"Gagal memproses data:\n{str(e)}")

    def on_download_error(self, err_msg):
        self.btn_download.setEnabled(True)
        self.progress_bar.hide()
        QMessageBox.critical(self, "Koneksi Gagal", err_msg)