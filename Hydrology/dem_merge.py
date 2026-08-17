import os
import rasterio
from rasterio.merge import merge
from rasterio.crs import CRS


class DEMMerger:
    """
    Menggabungkan beberapa DEM menjadi satu GeoTIFF.

    Khusus DEMNAS:
    - Banyak file DEMNAS tidak menyimpan CRS metadata.
    - Koordinat raster DEMNAS tetap menggunakan lon/lat WGS84.
    - Jika CRS kosong, output akan diberi CRS EPSG:4326
      agar kompatibel dengan WhiteboxTools.
    """

    def __init__(self, dem_files):
        self.dem_files = dem_files

    def merge(self, output_path="output/merged_dem.tif"):

        src_files_to_mosaic = []

        try:

            if not self.dem_files:
                raise ValueError(
                    "Tidak ada DEM yang diberikan untuk merge."
                )

            print()
            print("=" * 60)
            print("DEM MERGE")
            print("=" * 60)

            # --------------------------------------------------
            # Buka semua DEM
            # --------------------------------------------------

            for fp in self.dem_files:

                if not os.path.exists(fp):
                    raise FileNotFoundError(
                        f"DEM tidak ditemukan: {fp}"
                    )

                print(
                    f"[OPEN] {os.path.basename(fp)}"
                )

                src = rasterio.open(fp)

                src_files_to_mosaic.append(src)

            # --------------------------------------------------
            # Tentukan CRS
            # --------------------------------------------------

            source_crs = None

            for src in src_files_to_mosaic:

                if src.crs is not None:

                    source_crs = src.crs

                    break

            # DEMNAS yang CRS-nya kosong dianggap WGS84
            if source_crs is None:

                source_crs = CRS.from_epsg(4326)

                print(
                    "[CRS] Semua DEM tidak memiliki CRS."
                )

                print(
                    "[CRS] Menggunakan EPSG:4326 "
                    "(WGS84 lon/lat)."
                )

            else:

                print(
                    f"[CRS] CRS ditemukan: "
                    f"{source_crs}"
                )

            # --------------------------------------------------
            # Merge
            # --------------------------------------------------

            print()
            print(
                f"[MERGE] Menggabungkan "
                f"{len(src_files_to_mosaic)} DEM..."
            )

            mosaic, out_trans = merge(
                src_files_to_mosaic,
                nodata=-9999
            )

            # --------------------------------------------------
            # Metadata
            # --------------------------------------------------

            out_meta = (
                src_files_to_mosaic[0]
                .meta
                .copy()
            )

            out_meta.update(
                {
                    "driver": "GTiff",
                    "height": mosaic.shape[1],
                    "width": mosaic.shape[2],
                    "transform": out_trans,
                    "crs": source_crs,
                    "nodata": -9999,
                    "compress": "lzw",
                    "BIGTIFF": "IF_SAFER"
                }
            )

            # --------------------------------------------------
            # Pastikan folder output ada
            # --------------------------------------------------

            output_path = os.path.abspath(
                output_path
            )

            output_dir = os.path.dirname(
                output_path
            )

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            # --------------------------------------------------
            # Tulis GeoTIFF
            # --------------------------------------------------

            print()
            print(
                "[WRITE] Menulis merged DEM:"
            )

            print(
                output_path
            )

            with rasterio.open(
                output_path,
                "w",
                **out_meta
            ) as dest:

                dest.write(mosaic)

            # --------------------------------------------------
            # Validasi output
            # --------------------------------------------------

            if not os.path.exists(
                output_path
            ):

                raise RuntimeError(
                    "File merged DEM gagal dibuat."
                )

            print()
            print(
                "[VALIDATE] Memeriksa metadata..."
            )

            with rasterio.open(
                output_path
            ) as check:

                print(
                    f"  CRS      : {check.crs}"
                )

                print(
                    f"  Width    : {check.width}"
                )

                print(
                    f"  Height   : {check.height}"
                )

                print(
                    f"  Transform: {check.transform}"
                )

                print(
                    f"  Bounds   : {check.bounds}"
                )

                if check.crs is None:

                    raise RuntimeError(
                        "Merged DEM masih tidak "
                        "memiliki CRS."
                    )

            print()
            print(
                "✓ DEM MERGE BERHASIL"
            )

            print(
                f"✓ Jumlah DEM : "
                f"{len(src_files_to_mosaic)}"
            )

            print(
                f"✓ Output     : "
                f"{output_path}"
            )

            print(
                f"✓ CRS        : "
                f"{source_crs}"
            )

            print("=" * 60)

            return output_path

        except Exception as e:

            print()
            print(
                "ERROR saat merge DEM:"
            )

            print(e)

            raise

        finally:

            # --------------------------------------------------
            # Tutup semua raster
            # --------------------------------------------------

            for src in src_files_to_mosaic:

                try:
                    src.close()

                except Exception:
                    pass