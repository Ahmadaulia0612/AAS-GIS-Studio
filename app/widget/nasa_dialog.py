import os
import json
import requests
import pandas as pd

from PySide6.QtCore import QDate, QThread, QObject, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QDateEdit,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QHBoxLayout,
    QWidget,
)


# ============================================================
# WORKER UNTUK DOWNLOAD DATA
# Supaya GUI tidak "Not Responding"
# ============================================================

class ClimateDownloadWorker(QObject):
    finished = Signal(object, object, str, str)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, source, lat, lon, start_date, end_date):
        super().__init__()

        self.source = source
        self.lat = float(lat)
        self.lon = float(lon)
        self.start_date = start_date
        self.end_date = end_date

    # --------------------------------------------------------
    # MAIN
    # --------------------------------------------------------

    def run(self):
        try:
            if self.source == "NASA":
                self.progress.emit("Mengambil data NASA POWER...")
                df = self.download_nasa()

                self.progress.emit("Membuat rekap bulanan...")
                monthly = self.make_monthly_recap(df)

                self.finished.emit(
                    df,
                    monthly,
                    "NASA",
                    "Data NASA"
                )

            elif self.source == "CHIRPS":
                self.progress.emit("Menghubungkan ke Climate Engine...")
                df = self.download_chirps()

                self.progress.emit("Membuat rekap bulanan...")
                monthly = self.make_monthly_recap(df)

                self.finished.emit(
                    df,
                    monthly,
                    "CHIRPS",
                    "Data CHIRPS Asli"
                )

        except Exception as e:
            self.error.emit(str(e))

    # ========================================================
    # NASA POWER
    # ========================================================

    def download_nasa(self):

        url = "https://power.larc.nasa.gov/api/temporal/daily/point"

        params = {
            # NASA dapat mengembalikan PRECTOTCORR
            "parameters": "PRECTOT",
            "community": "AG",

            # PENTING:
            # longitude dulu sesuai API
            "longitude": self.lon,
            "latitude": self.lat,

            "start": self.start_date.replace("-", ""),
            "end": self.end_date.replace("-", ""),

            "format": "JSON"
        }

        response = requests.get(
            url,
            params=params,
            timeout=180
        )

        if response.status_code != 200:
            raise Exception(
                f"NASA POWER gagal.\n\n"
                f"HTTP: {response.status_code}\n"
                f"{response.text[:1000]}"
            )

        try:
            data = response.json()
        except Exception:
            raise Exception(
                "NASA mengembalikan respons yang bukan JSON."
            )

        # ----------------------------------------------------
        # Ambil parameter
        # ----------------------------------------------------

        parameters_data = (
            data
            .get("properties", {})
            .get("parameter", {})
        )

        if not parameters_data:
            raise Exception(
                "Data parameter NASA kosong.\n\n"
                f"Respons:\n{json.dumps(data, indent=2)[:2000]}"
            )

        # ----------------------------------------------------
        # PRIORITAS PRECTOTCORR
        # ----------------------------------------------------

        if "PRECTOTCORR" in parameters_data:

            rainfall = parameters_data["PRECTOTCORR"]

        elif "PRECTOT" in parameters_data:

            rainfall = parameters_data["PRECTOT"]

        else:

            available = list(parameters_data.keys())

            raise Exception(
                "Parameter curah hujan NASA tidak ditemukan.\n\n"
                f"Parameter tersedia: {available}"
            )

        # ----------------------------------------------------
        # DataFrame
        # ----------------------------------------------------

        rows = []

        for date_str, value in rainfall.items():

            try:
                value = float(value)
            except Exception:
                value = 0.0

            rows.append({
                "Periode": date_str,
                "Precipitation (mm)": value
            })

        if not rows:
            raise Exception(
                "NASA tidak mengembalikan data curah hujan."
            )

        df = pd.DataFrame(rows)

        df["Periode"] = pd.to_datetime(
            df["Periode"],
            errors="coerce"
        )

        df["Precipitation (mm)"] = pd.to_numeric(
            df["Precipitation (mm)"],
            errors="coerce"
        ).fillna(0.0)

        df = df.dropna(
            subset=["Periode"]
        )

        df = df.sort_values(
            "Periode"
        ).reset_index(drop=True)

        return df

    # ========================================================
    # CLIMATE ENGINE / CHIRPS
    # ========================================================

    def download_chirps(self):

        url = (
            "https://api.climateengine.org/"
            "timeseries/native/coordinates"
        )

        # ----------------------------------------------------
        # API KEY
        # ----------------------------------------------------

        api_key = os.environ.get(
            "CLIMATE_ENGINE_API_KEY",
            ""
        ).strip()

        if not api_key:
            raise Exception(
                "CLIMATE_ENGINE_API_KEY tidak ditemukan.\n\n"
                "Pastikan environment variable sudah di-set."
            )

        # ----------------------------------------------------
        # KOORDINAT
        #
        # longitude, latitude
        #
        # otomatis memakai Outlet KML
        # ----------------------------------------------------

        coordinates = json.dumps([
            [
                float(self.lon),
                float(self.lat)
            ]
        ])

        payload = {
            "coordinates": coordinates,
            "simplify_geometry": None,
            "buffer": None,
            "area_reducer": "mean",
            "dataset": "CHIRPS_DAILY",
            "variable": "precipitation",
            "compute_trends": "",
            "mask_image_id": "",
            "mask_band": "",
            "mask_value": None,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "export_path": "",
            "export_format": ""
        }

        # ====================================================
        # PENTING
        #
        # Climate Engine berhasil ketika:
        #
        # Authorization = API KEY
        #
        # BUKAN:
        #
        # Authorization = Bearer API KEY
        # ====================================================

        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=300
        )

        # ----------------------------------------------------
        # ERROR HANDLING
        # ----------------------------------------------------

        if response.status_code == 401:

            raise Exception(
                "Climate Engine menolak API key.\n\n"
                "HTTP: 401\n"
                "Invalid API token.\n\n"
                "Tetapi jika validate_key menghasilkan HTTP 200, "
                "pastikan aplikasi memakai environment variable "
                "CLIMATE_ENGINE_API_KEY yang sama."
            )

        if response.status_code != 200:

            raise Exception(
                "Climate Engine gagal.\n\n"
                f"HTTP: {response.status_code}\n\n"
                f"{response.text[:3000]}"
            )

        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        try:
            result = response.json()
        except Exception:

            raise Exception(
                "Respons Climate Engine bukan JSON.\n\n"
                f"{response.text[:2000]}"
            )

        # ----------------------------------------------------
        # Struktur:
        #
        # Data
        #   [0]
        #     Data
        #       [
        #         {
        #           Date: ...
        #           precipitation (mm): ...
        #         }
        #       ]
        # ----------------------------------------------------

        try:

            raw_data = (
                result["Data"][0]["Data"]
            )

        except Exception:

            raise Exception(
                "Format data Climate Engine tidak sesuai.\n\n"
                f"{json.dumps(result, indent=2)[:4000]}"
            )

        if not raw_data:

            raise Exception(
                "Climate Engine tidak mengembalikan data."
            )

        df = pd.DataFrame(raw_data)

        # ----------------------------------------------------
        # Nama kolom Climate Engine
        # ----------------------------------------------------

        if "Date" not in df.columns:

            raise Exception(
                "Kolom Date tidak ditemukan dari Climate Engine.\n\n"
                f"Kolom tersedia: {list(df.columns)}"
            )

        # API saat ini mengembalikan:
        #
        # precipitation (mm)
        #
        # bukan hanya "precipitation"
        #

        precipitation_column = None

        for col in df.columns:

            if str(col).lower() in [
                "precipitation",
                "precipitation (mm)"
            ]:
                precipitation_column = col
                break

        if precipitation_column is None:

            raise Exception(
                "Kolom precipitation tidak ditemukan.\n\n"
                f"Kolom tersedia: {list(df.columns)}"
            )

        df = df.rename(
            columns={
                "Date": "Periode",
                precipitation_column: "Precipitation (mm)"
            }
        )

        # ----------------------------------------------------
        # Bersihkan
        # ----------------------------------------------------

        df["Periode"] = pd.to_datetime(
            df["Periode"],
            errors="coerce"
        )

        df["Precipitation (mm)"] = pd.to_numeric(
            df["Precipitation (mm)"],
            errors="coerce"
        ).fillna(0.0)

        df = df.dropna(
            subset=["Periode"]
        )

        df = df.sort_values(
            "Periode"
        ).reset_index(drop=True)

        return df

    # ========================================================
    # REKAP BULANAN
    # ========================================================

    def make_monthly_recap(self, df):

        temp = df.copy()

        temp["YEAR"] = (
            temp["Periode"].dt.year
        )

        temp["MONTH"] = (
            temp["Periode"].dt.month
        )

        # ----------------------------------------------------
        # Pivot
        # ----------------------------------------------------

        monthly = temp.pivot_table(
            index="YEAR",
            columns="MONTH",
            values="Precipitation (mm)",
            aggfunc="sum",
            fill_value=0
        )

        # Pastikan 12 bulan selalu ada
        for month in range(1, 13):

            if month not in monthly.columns:
                monthly[month] = 0.0

        monthly = monthly[
            list(range(1, 13))
        ]

        month_names = [
            "JAN",
            "FEB",
            "MAR",
            "APR",
            "MAY",
            "JUN",
            "JUL",
            "AUG",
            "SEP",
            "OCT",
            "NOV",
            "DEC"
        ]

        monthly.columns = month_names

        # ----------------------------------------------------
        # ANN
        # ----------------------------------------------------

        monthly["ANN"] = monthly[
            month_names
        ].sum(axis=1)

        monthly = monthly.reset_index()

        return monthly

    # ========================================================
    # SIMPAN EXCEL
    # ========================================================

    @staticmethod
    def save_excel(
        filepath,
        df,
        monthly,
        sheet_title,
        source_name,
        lat,
        lon,
        start_date,
        end_date
    ):

        from openpyxl import load_workbook
        from openpyxl.styles import Font, Alignment

        # ----------------------------------------------------
        # Format daily
        # ----------------------------------------------------

        daily = df.copy()

        daily["Periode"] = (
            daily["Periode"]
            .dt.strftime("%Y-%m-%d")
        )

        # ----------------------------------------------------
        # Excel writer
        # ----------------------------------------------------

        with pd.ExcelWriter(
            filepath,
            engine="openpyxl"
        ) as writer:

            daily.to_excel(
                writer,
                sheet_name=sheet_title,
                index=False,
                startrow=0,
                startcol=0
            )

        # ----------------------------------------------------
        # Styling
        # ----------------------------------------------------

        wb = load_workbook(filepath)

        ws = wb[sheet_title]

        # ----------------------------------------------------
        # Header informasi
        # ----------------------------------------------------

        ws["A1"] = "Periode"
        ws["B1"] = "Precipitation (mm)"

        # Rekap dimulai kolom E
        ws["E1"] = "HASIL REKAPITULASI BULAN"

        # Header rekap
        recap_headers = [
            "YEAR",
            "JAN",
            "FEB",
            "MAR",
            "APR",
            "MAY",
            "JUN",
            "JUL",
            "AUG",
            "SEP",
            "OCT",
            "NOV",
            "DEC",
            "ANN"
        ]

        for col_idx, header in enumerate(
            recap_headers,
            start=5
        ):

            cell = ws.cell(
                row=2,
                column=col_idx
            )

            cell.value = header
            cell.font = Font(
                bold=True
            )

        # ----------------------------------------------------
        # Data rekap
        # ----------------------------------------------------

        for r_idx, row in monthly.iterrows():

            for c_idx, value in enumerate(
                row,
                start=5
            ):

                cell = ws.cell(
                    row=r_idx + 3,
                    column=c_idx
                )

                cell.value = (
                    float(value)
                    if pd.notna(value)
                    else 0.0
                )

        # ----------------------------------------------------
        # Info koordinat
        # ----------------------------------------------------

        info_row = 1

        ws["T1"] = "SOURCE"
        ws["U1"] = source_name

        ws["T2"] = "LATITUDE"
        ws["U2"] = float(lat)

        ws["T3"] = "LONGITUDE"
        ws["U3"] = float(lon)

        ws["T4"] = "START"
        ws["U4"] = start_date

        ws["T5"] = "END"
        ws["U5"] = end_date

        for cell in [
            ws["T1"],
            ws["T2"],
            ws["T3"],
            ws["T4"],
            ws["T5"]
        ]:

            cell.font = Font(
                bold=True
            )

        # ----------------------------------------------------
        # Lebar kolom
        # ----------------------------------------------------

        ws.column_dimensions["A"].width = 15
        ws.column_dimensions["B"].width = 22

        for col in range(5, 19):

            ws.column_dimensions[
                ws.cell(
                    row=1,
                    column=col
                ).column_letter
            ].width = 12

        ws.column_dimensions["T"].width = 15
        ws.column_dimensions["U"].width = 22

        # ----------------------------------------------------
        # Format angka
        # ----------------------------------------------------

        for row in ws.iter_rows(
            min_row=3,
            min_col=2,
            max_col=2
        ):

            for cell in row:

                if isinstance(
                    cell.value,
                    (int, float)
                ):
                    cell.number_format = "0.####"

        for row in ws.iter_rows(
            min_row=3,
            min_col=6,
            max_col=18
        ):

            for cell in row:

                if isinstance(
                    cell.value,
                    (int, float)
                ):
                    cell.number_format = "0.####"

        # ----------------------------------------------------
        # Freeze pane
        # ----------------------------------------------------

        ws.freeze_panes = "A2"

        wb.save(filepath)


# ============================================================
# DIALOG
# ============================================================

class ClimateDataDownloadDialog(QDialog):

    def __init__(
        self,
        lat,
        lon,
        parent=None
    ):

        super().__init__(parent)

        # ----------------------------------------------------
        # KOORDINAT DARI OUTLET KML
        # ----------------------------------------------------

        self.lat = float(lat)
        self.lon = float(lon)

        self.thread = None
        self.worker = None

        self.setWindowTitle(
            "Unduh Data Iklim Presisi (NASA & CHIRPS)"
        )

        self.setFixedSize(
            500,
            390
        )

        self.init_ui()

    # ========================================================
    # UI
    # ========================================================

    def init_ui(self):

        layout = QVBoxLayout(self)

        # ----------------------------------------------------
        # Koordinat
        # ----------------------------------------------------

        self.lbl_info = QLabel(
            "<b>Koordinat Target:</b><br>"
            f"Latitude: {self.lat:.4f}<br>"
            f"Longitude: {self.lon:.4f}"
        )

        layout.addWidget(
            self.lbl_info
        )

        # ----------------------------------------------------
        # Source
        # ----------------------------------------------------

        layout.addWidget(
            QLabel("Pilih Sumber Data:")
        )

        self.combo_source = QComboBox()

        self.combo_source.addItems([
            "NASA POWER (Unduh Online)",
            "CHIRPS Asli (Climate Engine API)"
        ])

        layout.addWidget(
            self.combo_source
        )

        # ----------------------------------------------------
        # Resolusi
        # ----------------------------------------------------

        layout.addWidget(
            QLabel("Pilih Resolusi Waktu:")
        )

        self.combo_interval = QComboBox()

        self.combo_interval.addItems([
            "Harian (Daily)",
            "Bulanan (Monthly)",
            "Tahunan (Annual)"
        ])

        # Kita prioritaskan data harian
        # karena rekap bulanan dibuat dari data harian.
        layout.addWidget(
            self.combo_interval
        )

        # ----------------------------------------------------
        # Tanggal
        # ----------------------------------------------------

        date_widget_container = QWidget()

        date_layout = QHBoxLayout(
            date_widget_container
        )

        date_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        # START
        v1 = QVBoxLayout()

        v1.addWidget(
            QLabel("Tanggal Mulai:")
        )

        self.date_start = QDateEdit(
            QDate(
                2010,
                1,
                1
            )
        )

        self.date_start.setCalendarPopup(
            True
        )

        self.date_start.setDisplayFormat(
            "dd/MM/yyyy"
        )

        v1.addWidget(
            self.date_start
        )

        # END
        v2 = QVBoxLayout()

        v2.addWidget(
            QLabel("Tanggal Selesai:")
        )

        self.date_end = QDateEdit(
            QDate(
                2025,
                12,
                31
            )
        )

        self.date_end.setCalendarPopup(
            True
        )

        self.date_end.setDisplayFormat(
            "dd/MM/yyyy"
        )

        v2.addWidget(
            self.date_end
        )

        date_layout.addLayout(v1)
        date_layout.addLayout(v2)

        layout.addWidget(
            date_widget_container
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self.lbl_status = QLabel(
            "Siap."
        )

        layout.addWidget(
            self.lbl_status
        )

        # ----------------------------------------------------
        # Button
        # ----------------------------------------------------

        self.btn_download = QPushButton(
            "📥 Unduh Otomatis & Simpan (.xlsx)"
        )

        self.btn_download.setStyleSheet(
            """
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }

            QPushButton:disabled {
                background-color: #555555;
            }
            """
        )

        self.btn_download.clicked.connect(
            self.process_download
        )

        layout.addWidget(
            self.btn_download
        )

    # ========================================================
    # DOWNLOAD
    # ========================================================

    def process_download(self):

        start_date = (
            self.date_start
            .date()
            .toString("yyyy-MM-dd")
        )

        end_date = (
            self.date_end
            .date()
            .toString("yyyy-MM-dd")
        )

        # ----------------------------------------------------
        # Validasi
        # ----------------------------------------------------

        if start_date > end_date:

            QMessageBox.warning(
                self,
                "Tanggal Salah",
                "Tanggal mulai tidak boleh lebih besar "
                "dari tanggal selesai."
            )

            return

        # ----------------------------------------------------
        # Source
        # ----------------------------------------------------

        source_idx = (
            self.combo_source.currentIndex()
        )

        source = (
            "NASA"
            if source_idx == 0
            else "CHIRPS"
        )

        # ----------------------------------------------------
        # Disable UI
        # ----------------------------------------------------

        self.btn_download.setEnabled(
            False
        )

        self.combo_source.setEnabled(
            False
        )

        self.combo_interval.setEnabled(
            False
        )

        self.date_start.setEnabled(
            False
        )

        self.date_end.setEnabled(
            False
        )

        self.lbl_status.setText(
            "Sedang menghubungkan ke server..."
        )

        # ----------------------------------------------------
        # Thread
        # ----------------------------------------------------

        self.thread = QThread()

        self.worker = ClimateDownloadWorker(
            source,
            self.lat,
            self.lon,
            start_date,
            end_date
        )

        self.worker.moveToThread(
            self.thread
        )

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.progress.connect(
            self.lbl_status.setText
        )

        self.worker.finished.connect(
            self.download_finished
        )

        self.worker.error.connect(
            self.download_error
        )

        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.error.connect(
            self.thread.quit
        )

        self.thread.finished.connect(
            self.thread_finished
        )

        self.thread.start()

    # ========================================================
    # SELESAI
    # ========================================================

    def download_finished(
        self,
        df,
        monthly,
        source,
        sheet_title
    ):

        self._df = df
        self._monthly = monthly
        self._source = source
        self._sheet_title = sheet_title

        self.lbl_status.setText(
            "Data berhasil diambil. Pilih lokasi penyimpanan..."
        )

        # ----------------------------------------------------
        # Nama file
        # ----------------------------------------------------

        if source == "NASA":

            default_name = (
                "nasa_rainfall_combined.xlsx"
            )

        else:

            default_name = (
                "chirps_rainfall_combined.xlsx"
            )

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan File Excel",
            default_name,
            "Excel Files (*.xlsx)"
        )

        if not filepath:

            self.reset_ui()

            return

        # ----------------------------------------------------
        # Simpan
        # ----------------------------------------------------

        try:

            ClimateDownloadWorker.save_excel(
                filepath=filepath,
                df=self._df,
                monthly=self._monthly,
                sheet_title=self._sheet_title,
                source_name=self._source,
                lat=self.lat,
                lon=self.lon,
                start_date=self.date_start.date().toString(
                    "yyyy-MM-dd"
                ),
                end_date=self.date_end.date().toString(
                    "yyyy-MM-dd"
                )
            )

            QMessageBox.information(
                self,
                "Berhasil",
                "Data berhasil diunduh dan disimpan.\n\n"
                f"Sumber: {self._source}\n"
                f"Koordinat:\n"
                f"Lat: {self.lat:.6f}\n"
                f"Lon: {self.lon:.6f}\n\n"
                f"Periode:\n"
                f"{self.date_start.date().toString('yyyy-MM-dd')}"
                " sampai "
                f"{self.date_end.date().toString('yyyy-MM-dd')}\n\n"
                f"Jumlah data harian: {len(self._df):,}\n\n"
                f"File:\n{filepath}"
            )

            self.accept()

        except Exception as e:

            QMessageBox.critical(
                self,
                "Gagal Menyimpan",
                str(e)
            )

            self.reset_ui()

    # ========================================================
    # ERROR
    # ========================================================

    def download_error(self, message):

        self.lbl_status.setText(
            "Gagal mengambil data."
        )

        QMessageBox.critical(
            self,
            "Gagal Mengambil Data",
            message
        )

        self.reset_ui()

    # ========================================================
    # THREAD SELESAI
    # ========================================================

    def thread_finished(self):

        if self.thread:

            self.thread.deleteLater()

        self.thread = None
        self.worker = None

    # ========================================================
    # RESET UI
    # ========================================================

    def reset_ui(self):

        self.btn_download.setEnabled(
            True
        )

        self.combo_source.setEnabled(
            True
        )

        self.combo_interval.setEnabled(
            True
        )

        self.date_start.setEnabled(
            True
        )

        self.date_end.setEnabled(
            True
        )

        self.btn_download.setText(
            "📥 Unduh Otomatis & Simpan (.xlsx)"
        )

        self.lbl_status.setText(
            "Siap."
        )