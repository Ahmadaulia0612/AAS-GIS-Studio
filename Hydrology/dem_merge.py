import os

from osgeo import gdal


class DEMMerger:

    def __init__(self):

        self.output_folder = "output"

        os.makedirs(
            self.output_folder,
            exist_ok=True
        )

    def merge(self, dem_files):

        if len(dem_files) == 0:
            raise Exception("DEM kosong")

        output_vrt = os.path.join(
            self.output_folder,
            "merged.vrt"
        )

        print("=" * 60)
        print("MERGING DEM")
        print("=" * 60)

        for f in dem_files:
            print(f)

        print("=" * 60)

        gdal.BuildVRT(
            output_vrt,
            dem_files
        )

        print("VRT :", output_vrt)

        return output_vrt