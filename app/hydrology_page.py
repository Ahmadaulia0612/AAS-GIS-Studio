from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox
)

import os


class HydrologyPage(QWidget):

    def __init__(self):
        super().__init__()

        self.dem_folder = None
        self.rbi_file = None

        layout = QVBoxLayout()

        self.btn_dem = QPushButton("Load DEM Folder")
        self.btn_rbi = QPushButton("Load RBI")

        self.lbl_dem = QLabel("DEM : -")
        self.lbl_rbi = QLabel("RBI : -")
        self.lbl_outlet = QLabel("Outlet : -")

        self.btn_run = QPushButton("Run Watershed")

        layout.addWidget(self.btn_dem)
        layout.addWidget(self.btn_rbi)

        layout.addWidget(self.lbl_dem)
        layout.addWidget(self.lbl_rbi)
        layout.addWidget(self.lbl_outlet)

        layout.addSpacing(20)

        layout.addWidget(self.btn_run)

        self.setLayout(layout)

        self.btn_dem.clicked.connect(self.load_dem_folder)
        self.btn_rbi.clicked.connect(self.load_rbi)

    def load_dem_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select DEM Folder"
        )

        if not folder:
            return

        tif_files = []

        for f in os.listdir(folder):
            if f.lower().endswith(".tif"):
                tif_files.append(f)

        if len(tif_files) == 0:

            QMessageBox.warning(
                self,
                "DEM",
                "Tidak ada file DEM (*.tif)"
            )
            return

        self.dem_folder = folder

        self.lbl_dem.setText(
            f"DEM : {len(tif_files)} tile"
        )

        print("DEM Folder :", folder)

        for f in tif_files:
            print(f)

    def load_rbi(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open RBI",
            "",
            "Shapefile (*.shp)"
        )

        if filename == "":
            return

        self.rbi_file = filename

        self.lbl_rbi.setText(
            filename
        )