import os
# Tambahkan flag Chromium tambahan untuk mengatasi kegagalan konteks GPU pada berbagai jenis PC/Laptop
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer --no-sandbox"

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from resource import resource_path
from app.main_window import MainWindow

# Analyzer
from modules.analyzer.polygon_analyzer import PolygonAnalyzer
from modules.analyzer.polygon_compare import PolygonCompare
from modules.analyzer.topology import TopologyAnalyzer


def main():
    # Aktifkan atribut high DPI jika didukung
    app = QApplication(sys.argv)

    app.setWindowIcon(
        QIcon(resource_path("icons/logo.ico"))
    )

    window = MainWindow()
    window.show()  

    print("\n===== POLYGON ANALYZER =====")
    try:
        PolygonAnalyzer().analyze("area_baku_sawah.shp")
    except Exception as e:
        print(f"Analyzer notice: {e}")

    print("\n===== POLYGON COMPARE =====")
    try:
        PolygonCompare("area_baku_sawah.shp").summary()
    except Exception as e:
        print(f"Compare notice: {e}")

    print("\n===== TOPOLOGY ANALYZER =====")
    try:
        TopologyAnalyzer("area_baku_sawah.shp").analyze()
    except Exception as e:
        print(f"Topology notice: {e}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()