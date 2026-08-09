import os
import shutil
import rasterio
from rasterio.merge import merge

class DEMMerger:
    def __init__(self):
        self.output_folder = "output"
        os.makedirs(self.output_folder, exist_ok=True)

    def merge(self, dem_files):
        if not dem_files:
            raise Exception("DEM kosong")

        print("=" * 60)
        print("MERGING DEM MENGGUNAKAN RASTERIO (ANTI-SPASI)")
        print("=" * 60)
        for f in dem_files:
            print(f)
        print("=" * 60)

        output_raster = os.path.join(self.output_folder, "merged_dem.tif")

        # Bersihkan sisa file lama
        if os.path.exists(output_raster):
            os.remove(output_raster)
        old_spasi = os.path.join(self.output_folder, "merged dem.tif")
        if os.path.exists(old_spasi):
            os.remove(old_spasi)

        if len(dem_files) == 1:
            shutil.copy(dem_files[0], output_raster)
        else:
            try:
                # Proses merge kebal spasi menggunakan rasterio
                src_files_to_mosaic = [rasterio.open(fp) for fp in dem_files]
                mosaic, out_trans = merge(src_files_to_mosaic)

                # Sesuaikan metadata
                out_meta = src_files_to_mosaic[0].meta.copy()
                out_meta.update({
                    "driver": "GTiff",
                    "height": mosaic.shape[1],
                    "width": mosaic.shape[2],
                    "transform": out_trans,
                })

                # Tulis file hasil merge
                with rasterio.open(output_raster, "w", **out_meta) as dest:
                    dest.write(mosaic)

                # Tutup semua file
                for src in src_files_to_mosaic:
                    src.close()
            except Exception as e:
                raise Exception(f"Gagal merge DEM: {e}")

        print("Merged DEM Raster :", output_raster)
        return output_raster