import os
import rasterio
from rasterio.merge import merge

class DEMMerger:
    """Kelas untuk menggabungkan beberapa file DEM menjadi satu file raster utuh"""
    def __init__(self, dem_files):
        self.dem_files = dem_files

    def merge(self, output_path="output/merged_dem.tif"):
        src_files_to_mosaic = []
        try:
            for fp in self.dem_files:
                src = rasterio.open(fp)
                src_files_to_mosaic.append(src)

            mosaic, out_trans = merge(src_files_to_mosaic, nodata=-9999)
            out_meta = src_files_to_mosaic[0].meta.copy()

            out_meta.update({
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": out_trans,
                "nodata": -9999
            })

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(mosaic)

            print(f"INFO: Berhasil menggabungkan {len(self.dem_files)} DEM ke {output_path}")
            return output_path

        except Exception as e:
            print(f"ERROR saat merge DEM: {e}")
            raise e
        finally:
            for src in src_files_to_mosaic:
                src.close()