import os
import geopandas as gpd


class Exporter:

    def export(self, output_folder, river_ln, river_ar=None):

        os.makedirs(output_folder, exist_ok=True)

        ln_file = None
        ar_file = None

        if river_ln is not None and len(river_ln) > 0:
            ln_file = os.path.join(output_folder, "river_ln.geojson")
            river_ln.to_file(
                ln_file,
                driver="GeoJSON"
            )

        if river_ar is not None and len(river_ar) > 0:
            ar_file = os.path.join(output_folder, "river_ar.geojson")
            river_ar.to_file(
                ar_file,
                driver="GeoJSON"
            )

        return ln_file, ar_file