import os
import geopandas as gpd
from shapely.geometry import shape


class SHPExporter:

    def export(self, geojson, output_folder, filename):

        os.makedirs(output_folder, exist_ok=True)

        features = []

        for feature in geojson["features"]:

            if feature["geometry"] is None:
                continue

            geom = shape(feature["geometry"])

            prop = feature["properties"].copy()

            prop["geometry"] = geom

            features.append(prop)

        gdf = gpd.GeoDataFrame(
            features,
            geometry="geometry",
            crs="EPSG:4326"
        )

        shp_path = os.path.join(
            output_folder,
            filename + ".shp"
        )

        gdf.to_file(
            shp_path,
            driver="ESRI Shapefile"
        )

        return shp_path