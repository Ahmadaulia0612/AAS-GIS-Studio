import geopandas as gpd
import fiona


class RiverReader:

    def load(self, gpkg):

        layers = fiona.listlayers(gpkg)

        print("Layers :", layers)

        river_ln = None
        river_ar = None

        for layer in layers:

            if "LN" in layer.upper():
                river_ln = gpd.read_file(gpkg, layer=layer)

            elif "AR" in layer.upper():
                river_ar = gpd.read_file(gpkg, layer=layer)

        return river_ln, river_ar