import geopandas as gpd


class PolygonCompare:

    def __init__(self, shp):

        self.gdf = gpd.read_file(shp)

    def summary(self):

        print("=" * 70)
        print("POLYGON SUMMARY")
        print("=" * 70)

        print("Feature :", len(self.gdf))

        print()

        print(self.gdf.columns.tolist())

        print()

        print(self.gdf.head())