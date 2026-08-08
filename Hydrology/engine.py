import os

from Hydrology.dem.dem_merge import DEMMerger
from Hydrology.river.reader import RiverReader
from Hydrology.exporter import Exporter


class HydrologyEngine:

    def __init__(self, dem_files, river_file, outlet):

        self.dem_files = dem_files
        self.river_file = river_file
        self.outlet = outlet

        self.temp = "Hydrology/temp"

        os.makedirs(self.temp, exist_ok=True)

    def run(self):

        print("=" * 60)
        print("STEP 1 : MERGE DEM")
        print("=" * 60)

        merger = DEMMerger()

        merged_dem = merger.merge(
            self.dem_files,
            os.path.join(
                self.temp,
                "merged_dem.tif"
            )
        )

        print("Merged DEM :", merged_dem)

        print("=" * 60)
        print("STEP 2 : LOAD RIVER")
        print("=" * 60)

        reader = RiverReader()

        river_ln, river_ar = reader.load(
            self.river_file
        )

        print("Jumlah Sungai LN :", len(river_ln))

        if river_ar is not None:
            print("Jumlah Sungai AR :", len(river_ar))

        exporter = Exporter()

        ln_geojson, ar_geojson = exporter.export(
            self.outlet,
            river_ln,
            river_ar
        )

        print("LN :", ln_geojson)
        print("AR :", ar_geojson)