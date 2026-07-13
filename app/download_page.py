from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QFileDialog,
)

from modules.downloader.query_builder import QueryBuilder
from modules.downloader.big_downloader import BIGDownloader
from modules.exporter.shp_exporter import SHPExporter

import shutil
import os


class DownloadPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Downloader Area Baku Sawah")
        title.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
        """)

        layout.addWidget(title)

        # ==========================
        # URL
        # ==========================

        layout.addWidget(QLabel("URL BHUMI"))

        self.url = QLineEdit()

        self.url.setPlaceholderText(
            "Paste URL BHUMI..."
        )

        layout.addWidget(self.url)

        # ==========================
        # Nama File
        # ==========================

        layout.addWidget(QLabel("Nama File"))

        self.filename = QLineEdit("area_baku_sawah")

        layout.addWidget(self.filename)

        # ==========================
        # Output Folder
        # ==========================

        layout.addWidget(QLabel("Folder Output"))

        row = QHBoxLayout()

        self.folder = QLineEdit()

        self.folder.setText(os.getcwd())

        row.addWidget(self.folder)

        browse = QPushButton("Browse")

        browse.clicked.connect(self.browse)

        row.addWidget(browse)

        layout.addLayout(row)

        # ==========================

        self.download = QPushButton("Download SHP")

        self.download.clicked.connect(
            self.start_download
        )

        layout.addWidget(self.download)

        self.status = QLabel("Ready")

        layout.addWidget(self.status)

        self.log = QTextEdit()

        self.log.setReadOnly(True)

        layout.addWidget(self.log)

    def browse(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Pilih Folder"
        )

        if folder:

            self.folder.setText(folder)

    def start_download(self):

        try:

            self.log.clear()

            self.status.setText("Parsing URL...")

            query = QueryBuilder().build(
                self.url.text()
            )

            self.log.append("OK URL berhasil diparsing")

            self.status.setText("Downloading...")

            geojson = BIGDownloader().download(query)

            self.log.append(
                f"Feature ditemukan : {len(geojson['features'])}"
            )

            self.status.setText("Export SHP...")

            filename = self.filename.text()

            SHPExporter().export(
                geojson,
                filename
            )

            # pindahkan file ke folder pilihan
            source = "output"

            target = self.folder.text()

            for ext in [
                ".shp",
                ".shx",
                ".dbf",
                ".prj"
            ]:

                src = os.path.join(
                    source,
                    filename + ext
                )

                if os.path.exists(src):

                    shutil.move(
                        src,
                        os.path.join(
                            target,
                            filename + ext
                        )
                    )

            self.status.setText("SELESAI")

            self.log.append("")
            self.log.append("SHP berhasil dibuat")

            self.log.append(target)

        except Exception as e:

            self.status.setText("ERROR")

            self.log.append(str(e))