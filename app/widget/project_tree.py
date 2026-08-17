from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem


class ProjectTree(QTreeWidget):

    def __init__(self):
        super().__init__()

        self.setHeaderHidden(True)

        # ======================================================
        # PROJECT TREE
        # ======================================================

        self.project = QTreeWidgetItem(
            ["Project"]
        )

        self.dem = QTreeWidgetItem(
            ["DEM"]
        )

        self.river = QTreeWidgetItem(
            ["River"]
        )

        self.watershed = QTreeWidgetItem(
            ["Watershed"]
        )

        self.project.addChild(
            self.dem
        )

        self.project.addChild(
            self.river
        )

        self.project.addChild(
            self.watershed
        )

        self.addTopLevelItem(
            self.project
        )

        self.expandAll()

    # ==========================================================
    # DEM
    # ==========================================================

    def add_dem(
        self,
        filename
    ):
        self.dem.addChild(
            QTreeWidgetItem(
                [filename]
            )
        )

    # ==========================================================
    # RIVER
    # ==========================================================

    def add_river(
        self,
        filename
    ):
        self.river.addChild(
            QTreeWidgetItem(
                [filename]
            )
        )

    # ==========================================================
    # WATERSHED FILE
    # ==========================================================

    def add_watershed(
        self,
        filename
    ):
        self.watershed.addChild(
            QTreeWidgetItem(
                [filename]
            )
        )

        self.watershed.setExpanded(
            True
        )

    # ==========================================================
    # CLEAR WATERSHED INFO
    # ==========================================================

    def clear_watershed_info(
        self
    ):
        """
        Menghapus informasi hasil Watershed lama,
        tetapi node Watershed tetap dipertahankan.
        """

        while self.watershed.childCount() > 0:

            self.watershed.removeChild(
                self.watershed.child(0)
            )

    # ==========================================================
    # WATERSHED RESULT
    # ==========================================================

    def set_watershed_info(
        self,
        area_km2,
        outlet=None,
        duration=None,
        status="READY"
    ):
        """
        Menampilkan ringkasan hasil Watershed
        langsung pada Project Tree.
        """

        # ------------------------------------------------------
        # Hapus hasil sebelumnya
        # ------------------------------------------------------

        self.clear_watershed_info()

        # ------------------------------------------------------
        # CATCHMENT AREA
        # ------------------------------------------------------

        ca_item = QTreeWidgetItem(
            [
                f"CA : {area_km2:.3f} km²"
            ]
        )

        self.watershed.addChild(
            ca_item
        )

        # ------------------------------------------------------
        # OUTLET
        # ------------------------------------------------------

        if outlet is not None:

            lat, lon = outlet

            outlet_item = QTreeWidgetItem(
                [
                    f"Outlet : "
                    f"{lat:.5f}, "
                    f"{lon:.5f}"
                ]
            )

            self.watershed.addChild(
                outlet_item
            )

        # ------------------------------------------------------
        # PROCESSING TIME
        # ------------------------------------------------------

        if duration is not None:

            # ----------------------------------------------
            # < 60 detik
            # ----------------------------------------------

            if duration < 60:

                time_text = (
                    f"{duration:.2f} detik"
                )

            # ----------------------------------------------
            # 60 detik - < 1 jam
            # ----------------------------------------------

            elif duration < 3600:

                minutes = (
                    duration / 60
                )

                time_text = (
                    f"{minutes:.2f} menit"
                )

            # ----------------------------------------------
            # >= 1 jam
            # ----------------------------------------------

            else:

                hours = int(
                    duration // 3600
                )

                minutes = (
                    duration % 3600
                ) / 60

                time_text = (
                    f"{hours} jam "
                    f"{minutes:.2f} menit"
                )

            time_item = QTreeWidgetItem(
                [
                    f"Waktu : {time_text}"
                ]
            )

            self.watershed.addChild(
                time_item
            )

        # ------------------------------------------------------
        # STATUS
        # ------------------------------------------------------

        if status == "READY":

            status_text = (
                "✓ READY"
            )

        elif status == "WARNING":

            status_text = (
                "⚠ WARNING"
            )

        elif status == "ERROR":

            status_text = (
                "✕ ERROR"
            )

        else:

            status_text = str(
                status
            )

        status_item = QTreeWidgetItem(
            [
                f"Status : {status_text}"
            ]
        )

        self.watershed.addChild(
            status_item
        )

        # ------------------------------------------------------
        # BUKA NODE WATERSHED
        # ------------------------------------------------------

        self.watershed.setExpanded(
            True
        )

        self.expandAll()