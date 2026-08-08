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

    app = QApplication(sys.argv)

    app.setWindowIcon(
        QIcon(resource_path("icons/logo.ico"))
    )

    window = MainWindow()
    window.show()  

    print("\n===== POLYGON ANALYZER =====")
    PolygonAnalyzer().analyze(
        "area_baku_sawah.shp"
    )

    print("\n===== POLYGON COMPARE =====")
    PolygonCompare(
        "area_baku_sawah.shp"
    ).summary()

    print("\n===== TOPOLOGY ANALYZER =====")
    TopologyAnalyzer(
        "area_baku_sawah.shp"
    ).analyze()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()