from rasterio.merge import merge
from rasterio.crs import CRS
import rasterio


class DEMMerger:

    def merge(self, dem_files, output_file):

        if len(dem_files) == 1:

            with rasterio.open(dem_files[0]) as src:

                profile = src.profile.copy()

                data = src.read()

                if profile.get("crs") is None:
                    profile["crs"] = CRS.from_epsg(4326)

            with rasterio.open(output_file, "w", **profile) as dst:
                dst.write(data)

            print("Merged :", output_file)

            return output_file

        src_files = []

        for f in dem_files:
            src_files.append(rasterio.open(f))

        mosaic, transform = merge(src_files)

        meta = src_files[0].meta.copy()

        crs = src_files[0].crs

        if crs is None:
            crs = CRS.from_epsg(4326)

        meta.update(
            driver="GTiff",
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            transform=transform,
            crs=crs,
            compress="lzw"
        )

        with rasterio.open(output_file, "w", **meta) as dst:
            dst.write(mosaic)

        for s in src_files:
            s.close()

