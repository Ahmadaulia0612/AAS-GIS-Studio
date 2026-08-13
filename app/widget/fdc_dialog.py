import os
import numpy as np
import pandas as pd
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


class FdcDialog(QDialog):
    def __init__(self, ca_km2=None, parent=None):
        super().__init__(parent)
        self.ca_km2 = ca_km2 if ca_km2 else 742.07
        self.setWindowTitle("Flow Duration Curve (FDC) & Analisis Debit Andalan")
        self.resize(950, 650)

        self.is_updating = False
        self.init_ui()
        self.load_initial_fdc_data()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("<b>Tabel Probabilitas & Debit FDC (Bisa Diedit)</b>"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Probabilitas", "Debit (m³/detik)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.table)

        self.lbl_info = QLabel()
        self.lbl_info.setStyleSheet("background: #f8f9fa; padding: 10px; border: 1px solid #ccc; font-family: monospace;")
        left_layout.addWidget(self.lbl_info)

        main_layout.addLayout(left_layout, 1)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("<b>Kurva Durasi Debit (FDC)</b>"))

        self.figure, self.ax = plt.subplots(figsize=(6, 5))
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)

        main_layout.addLayout(right_layout, 2)

        self.table.itemChanged.connect(self.on_table_item_changed)

    def load_initial_fdc_data(self):
        csv_path = os.path.abspath("output/nasa_rainfall_data.csv")
        if not os.path.exists(csv_path):
            QMessageBox.warning(self, "Data Tidak Ditemukan", "File CSV data hujan NASA belum tersedia. Silakan unduh terlebih dahulu.")
            return

        try:
            df = pd.read_csv(csv_path)
            if "Curah_Hujan_mm" in df.columns:
                rainfall_series = df["Curah_Hujan_mm"]
            else:
                rainfall_series = df.iloc[:, 1]

            rainfall_series = pd.to_numeric(rainfall_series, errors='coerce').fillna(0)

            runoff_coeff = 0.65
            discharge = (rainfall_series * self.ca_km2 * 1000 * runoff_coeff) / 86400.0

            sorted_q = np.sort(discharge.values)[::-1]
            n = len(sorted_q)
            if n == 0:
                return

            probabilities = np.linspace(0, 100, 21)
            table_data = []

            for p in probabilities:
                idx = int(np.floor((p / 100.0) * (n - 1)))
                idx = max(0, min(idx, n - 1))
                q_val = sorted_q[idx]
                table_data.append((f"{int(p)}%", f"{q_val:.3f}"))

            self.is_updating = True
            self.table.setRowCount(len(table_data))
            for row_idx, (p_str, q_str) in enumerate(table_data):
                item_p = QTableWidgetItem(p_str)
                # Kunci kolom probabilitas agar tidak bisa diedit (hanya bisa dibaca)
                from PySide6.QtCore import Qt
                item_p.setFlags(item_p.flags() & ~Qt.ItemIsEditable)
                
                item_q = QTableWidgetItem(q_str)     # Kolom debit bisa diedit
                
                self.table.setItem(row_idx, 0, item_p)
                self.table.setItem(row_idx, 1, item_q)
            self.is_updating = False

            self.update_chart_from_table()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def on_table_item_changed(self, item):
        if self.is_updating:
            return
        if item.column() == 1:
            self.update_chart_from_table()

    def update_chart_from_table(self):
        try:
            row_count = self.table.rowCount()
            prob_points = []
            debit_points = []

            for row in range(row_count):
                p_item = self.table.item(row, 0)
                q_item = self.table.item(row, 1)

                if p_item and q_item:
                    p_val = float(p_item.text().replace("%", ""))
                    q_val = float(q_item.text()) if q_item.text() else 0.0
                    
                    prob_points.append(p_val)
                    debit_points.append(q_val)

            if not debit_points:
                return

            mean_q = np.mean(debit_points)
            spec_runoff = mean_q / self.ca_km2 if self.ca_km2 > 0 else 0

            info_text = (
                f"Mean Q         : {mean_q:.3f} m³/s\n"
                f"Catchment Area : {self.ca_km2:.2f} km²\n"
                f"Spec. Runoff   : {spec_runoff:.3f} m³/s/km²"
            )
            self.lbl_info.setText(info_text)

            self.ax.clear()
            self.ax.plot(prob_points, debit_points, marker='o', color='#0066cc', linestyle='-', linewidth=2, markersize=4)
            self.ax.set_title("Flow Duration Curve (FDC) - NASA POWER", fontsize=11, fontweight='bold')
            self.ax.set_xlabel("Probabilitas (%)", fontweight='bold')
            self.ax.set_ylabel("Debit (m³/detik)", fontweight='bold')
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.figure.tight_layout()
            self.canvas.draw()

        except ValueError:
            pass