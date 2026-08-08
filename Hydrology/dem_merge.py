import os
import whitebox


class DEMMerger:

    def __init__(self):
        self.output_folder = "output"
        os.makedirs(self.output_folder, exist_ok=True)
        
        # Inisialisasi WhiteboxTools
        self.wbt = whitebox.WhiteboxTools()
        self.wbt.set_verbose_mode(False)

    def merge(self, dem_files):
        if len(dem_files) == 0:
            raise Exception("DEM kosong")

        print("=" * 60)
        print("MERGING DEM MENGGUNAKAN WHITEBOX")
        print("=" * 60)

        for f in dem_files:
            print(f)

        print("=" * 60)

        # Output file raster hasil merge
        output_raster = os.path.join(self.output_folder, "merged_dem.tif")

        # Jika hanya ada 1 file DEM, salin atau jadikan output langsung
        if len(dem_files) == 1:
            import shutil
            shutil.copy(dem_files[0], output_raster)
        else:
            # Jika lebih dari 1 file DEM, gunakan fungsi Mosaic dari Whitebox
            # Whitebox memerlukan string input berupa path file yang dipisahkan koma atau list
            # Format whitebox mosaic memerlukan input string semicolon/komar-separated tergantung fungsi
            input_str = ";".join(dem_files)
            
            # Whitebox mosaic / mosaic_raster_tiles
            # Alternatif paling aman jika mosaic bawaan butuh format tertentu: 
            # Kita bisa pakai mosaic whitebox atau simply pass list jika didukung.
            # Mari kita gunakan fungsi mosaic whitebox:
            self.wbt.mosaic(
                inputs=input_str,
                output=output_raster
            )

        print("Merged DEM Raster :", output_raster)

        return output_raster