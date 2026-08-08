from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem


class ProjectTree(QTreeWidget):

    def __init__(self):
        super().__init__()

        self.setHeaderHidden(True)

        self.project = QTreeWidgetItem(["Project"])

        self.dem = QTreeWidgetItem(["DEM"])
        self.river = QTreeWidgetItem(["River"])
        self.watershed = QTreeWidgetItem(["Watershed"])
        self.stream = QTreeWidgetItem(["Stream"])
        self.export = QTreeWidgetItem(["Export"])

        self.project.addChild(self.dem)
        self.project.addChild(self.river)
        self.project.addChild(self.watershed)
        self.project.addChild(self.stream)
        self.project.addChild(self.export)

        self.addTopLevelItem(self.project)

        self.expandAll()

    def add_dem(self, filename):

        self.dem.addChild(
            QTreeWidgetItem([filename])
        )

    def add_river(self, filename):

        self.river.addChild(
            QTreeWidgetItem([filename])
        )

    def add_watershed(self, filename):

        self.watershed.addChild(
            QTreeWidgetItem([filename])
        )

    def add_stream(self, filename):

        self.stream.addChild(
            QTreeWidgetItem([filename])
        )