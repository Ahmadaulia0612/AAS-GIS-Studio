import rasterio


class DEMLoader:

    def __init__(self):
        self.dataset = None

    def open(self, filename):

        self.dataset = rasterio.open(filename)

        print("=" * 60)
        print("DEM INFORMATION")
        print("=" * 60)

        print("Width :", self.dataset.width)
        print("Height:", self.dataset.height)
        print("CRS   :", self.dataset.crs)
        print("Bounds:", self.dataset.bounds)
        print("Res   :", self.dataset.res)

        return self.dataset