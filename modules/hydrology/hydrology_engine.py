from modules.hydrology.dem_loader import DEMLoader


class HydrologyEngine:

    def __init__(self):

        self.dem = None

    def load_dem(self, filename):

        loader = DEMLoader()

        self.dem = loader.open(filename)

        print()

        print("DEM Loaded Successfully")

        return self.dem