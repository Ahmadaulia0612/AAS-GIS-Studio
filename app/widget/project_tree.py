from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem


class ProjectTree(QTreeWidget):

    def __init__(self):
        super().__init__()

        self.setHeaderHidden(True)

        self.project = QTreeWidgetItem(["Project"])

        self.dem = QTreeWidgetItem(["DEM"])
        self.river = QTreeWidgetItem(["River"])
        self.watershed = QTreeWidgetItem(["Watershed"])

        self.project.addChild(self.dem)
        self.project.addChild(self.river)
        self.project.addChild(self.watershed)

        self.addTopLevelItem(self.project)

        self.expandAll()

    def add_dem(self, filename):
        pass

    def add_river(self, filename):
        pass

    def add_watershed(self, filename):
        self.watershed.addChild(
            QTreeWidgetItem([filename])
        )