import os
import geopandas as gpd
import rasterio
from rasterio.warp import transform_bounds
from shapely.geometry import Point, box
import numpy as np

from Hydrology.dem_merge import DEMMerger
import whitebox


class HydrologyEngine:
    def __init__(self, dem_files, river_file, outlet):
        self.dem_files = dem_files
        self.river_file = river_file
        self.outlet = outlet  # (lat, lon)

        self.wbt = whitebox.WhiteboxTools()
        self.wbt.set_verbose_mode(True)

        os.makedirs("output", exist_ok=True)

        self.merged_dem = os.path.abspath(
            "output/merged_dem.tif"
        )

        self.last_area_km2 = 0.0

        # DEM yang benar-benar digunakan dalam analisis
        self.selected_dem_files = []

    # ==========================================================
    # DEM BOUNDS
    # ==========================================================

    def _dem_bounds_wgs84(self, dem_file):
        """
        Mengambil bounding box DEM dalam EPSG:4326.

        Jika DEM mempunyai CRS:
            bounds ditransformasikan ke WGS84.

        Jika DEM tidak mempunyai CRS:
            dianggap sudah menggunakan koordinat
            longitude/latitude WGS84.

        DEMNAS tertentu memang tidak menyimpan CRS
        pada metadata GeoTIFF.
        """

        with rasterio.open(dem_file) as src:

            if src.crs is None:

                bounds = src.bounds

                return box(
                    bounds.left,
                    bounds.bottom,
                    bounds.right,
                    bounds.top
                )

            bounds = transform_bounds(
                src.crs,
                "EPSG:4326",
                *src.bounds,
                densify_pts=21
            )

            return box(
                bounds[0],
                bounds[1],
                bounds[2],
                bounds[3]
            )

    # ==========================================================
    # DEM SELECTION
    # ==========================================================

    def _select_initial_dems(self):
        """
        Mencari DEM yang mencakup titik outlet.

        Tidak membaca seluruh raster.
        Hanya membaca metadata dan bounds.
        """

        lat, lon = self.outlet

        outlet_point = Point(
            float(lon),
            float(lat)
        )

        containing = []

        print()
        print("=" * 60)
        print("AUTO DEM SELECTION")
        print("=" * 60)

        print(
            f"Outlet            : "
            f"{lat}, {lon}"
        )

        print(
            f"Total DEM tersedia : "
            f"{len(self.dem_files)}"
        )

        for dem in self.dem_files:

            try:

                if not os.path.exists(dem):
                    print(
                        f"[SKIP] Tidak ditemukan: {dem}"
                    )
                    continue

                bounds = self._dem_bounds_wgs84(
                    dem
                )

                if bounds.covers(outlet_point):

                    containing.append(dem)

                    print(
                        "[USE] "
                        f"{os.path.basename(dem)}"
                    )

                else:

                    print(
                        "[SKIP] "
                        f"{os.path.basename(dem)}"
                    )

            except Exception as e:

                print(
                    "[WARNING] Gagal membaca DEM:"
                )

                print(
                    f"          {dem}"
                )

                print(
                    f"          {e}"
                )

        print()
        print(
            f"DEM yang mencakup outlet : "
            f"{len(containing)}"
        )

        if not containing:

            raise RuntimeError(
                "Tidak ada DEM yang mencakup "
                "titik outlet."
            )

        return containing

    # ==========================================================
    # FIND NEIGHBOUR DEM
    # ==========================================================

    def _expand_dem_selection(self, selected):
        """
        Menambahkan DEM tetangga yang bersentuhan
        dengan area DEM yang sedang digunakan.

        DEM asli tidak dihapus.
        """

        selected_abs = set(
            os.path.abspath(x)
            for x in selected
        )

        selected_boxes = []

        for dem in selected:

            try:

                selected_boxes.append(
                    self._dem_bounds_wgs84(dem)
                )

            except Exception as e:

                print(
                    f"[WARNING] Tidak bisa membaca "
                    f"bounds {dem}: {e}"
                )

        if not selected_boxes:
            return selected

        combined = selected_boxes[0]

        for b in selected_boxes[1:]:

            combined = combined.union(b)

        # Buffer kecil untuk menghindari masalah
        # floating point pada batas tile.
        expanded_area = combined.buffer(
            0.00001
        )

        new_selected = list(selected)

        print()
        print(
            "[SEARCH] Mencari DEM tetangga..."
        )

        for dem in self.dem_files:

            abs_dem = os.path.abspath(dem)

            if abs_dem in selected_abs:
                continue

            try:

                dem_box = self._dem_bounds_wgs84(
                    dem
                )

                if dem_box.intersects(
                    expanded_area
                ):

                    new_selected.append(dem)

                    selected_abs.add(abs_dem)

                    print(
                        "[+] Tambah DEM: "
                        f"{os.path.basename(dem)}"
                    )

            except Exception as e:

                print(
                    f"[WARNING] Gagal memeriksa "
                    f"{dem}: {e}"
                )

        return new_selected

    # ==========================================================
    # MAIN HYDROLOGY WORKFLOW
    # ==========================================================

    def run(self):

        print()
        print("=" * 60)
        print(
            "HYDROLOGY ENGINE"
        )
        print(
            "AUTO DEM SELECTION + WATERSHED"
        )
        print("=" * 60)

        # ------------------------------------------------------
        # STEP 1
        # Cari DEM yang mengandung outlet
        # ------------------------------------------------------

        selected = self._select_initial_dems()

        max_iterations = 5

        for iteration in range(
            1,
            max_iterations + 1
        ):

            print()
            print("=" * 60)
            print(
                f"WATERSHED ITERATION "
                f"{iteration}/{max_iterations}"
            )
            print("=" * 60)

            print(
                f"DEM yang digunakan : "
                f"{len(selected)}"
            )

            for dem in selected:

                print(
                    f"  - "
                    f"{os.path.basename(dem)}"
                )

            self.selected_dem_files = list(
                selected
            )

            # --------------------------------------------------
            # STEP 2
            # Merge hanya DEM yang terpilih
            # --------------------------------------------------

            print()
            print(
                "[1/3] Menggabungkan DEM "
                "yang diperlukan..."
            )

            merger = DEMMerger(
                dem_files=selected
            )

            self.merged_dem = merger.merge(
                output_path=os.path.abspath(
                    "output/merged_dem.tif"
                )
            )

            if not os.path.exists(
                self.merged_dem
            ):

                raise RuntimeError(
                    "merged_dem.tif gagal dibuat."
                )

            # --------------------------------------------------
            # STEP 3
            # Terrain analysis
            # --------------------------------------------------

            print()
            print(
                "[2/3] Analisis hidrologi terrain..."
            )

            (
                dem_filled,
                flow_dir,
                flow_acc
            ) = self.run_hydrology_steps(
                self.merged_dem
            )

            # --------------------------------------------------
            # STEP 4
            # Watershed
            # --------------------------------------------------

            print()
            print(
                "[3/3] Delineasi watershed..."
            )

            lat, lon = self.outlet

            result = self.delineate_watershed(
                flow_dir,
                flow_acc,
                lat,
                lon,
                return_edge_status=True
            )

            if result is None:

                raise RuntimeError(
                    "Watershed gagal dibuat."
                )

            area_km2, touches_edge = result

            # --------------------------------------------------
            # COVERAGE VALID
            # --------------------------------------------------

            if not touches_edge:

                print()
                print("=" * 60)
                print(
                    "✓ DEM COVERAGE CUKUP"
                )
                print(
                    f"✓ CA = "
                    f"{area_km2:.3f} km²"
                )
                print(
                    f"✓ DEM digunakan = "
                    f"{len(selected)}"
                )
                print("=" * 60)

                return area_km2

            # --------------------------------------------------
            # COVERAGE BELUM CUKUP
            # --------------------------------------------------

            print()
            print("=" * 60)
            print(
                "⚠ WATERSHED MENYENTUH "
                "BATAS DEM"
            )
            print(
                "⚠ Coverage belum dapat "
                "dianggap lengkap."
            )
            print("=" * 60)

            expanded = (
                self._expand_dem_selection(
                    selected
                )
            )

            # Tidak ada DEM tambahan
            if len(expanded) == len(selected):

                raise RuntimeError(
                    "Watershed menyentuh batas "
                    "DEM tetapi tidak ada DEM "
                    "tambahan yang tersedia."
                )

            selected = expanded

        raise RuntimeError(
            "Maksimum iterasi pemilihan DEM "
            "tercapai. Coverage watershed "
            "belum dapat dipastikan."
        )

    # ==========================================================
    # TERRAIN PROCESSING
    # ==========================================================

    def run_hydrology_steps(
        self,
        dem_input
    ):

        base_dir = os.path.abspath(
            "output"
        )

        dem_filled = os.path.join(
            base_dir,
            "dem_filled.tif"
        )

        flow_dir = os.path.join(
            base_dir,
            "flow_dir.tif"
        )

        flow_acc = os.path.join(
            base_dir,
            "flow_acc.tif"
        )

        # ------------------------------------------------------
        # Hapus hasil lama
        # ------------------------------------------------------

        for f in [
            dem_filled,
            flow_dir,
            flow_acc
        ]:

            if os.path.exists(f):

                try:
                    os.remove(f)

                except Exception as e:

                    raise RuntimeError(
                        f"Gagal menghapus "
                        f"file lama {f}: {e}"
                    )

        abs_dem = os.path.abspath(
            dem_input
        )

        if not os.path.exists(
            abs_dem
        ):

            raise FileNotFoundError(
                f"DEM tidak ditemukan: "
                f"{abs_dem}"
            )

        abs_filled = os.path.abspath(
            dem_filled
        )

        abs_flow_dir = os.path.abspath(
            flow_dir
        )

        abs_flow_acc = os.path.abspath(
            flow_acc
        )

        print()
        print(
            "DEM yang diproses:"
        )

        print(abs_dem)

        # ------------------------------------------------------
        # Breach Depressions
        # ------------------------------------------------------

        print()
        print(
            "[1] Breach Depressions..."
        )

        self.wbt.breach_depressions(
            dem=abs_dem,
            output=abs_filled
        )

        if not os.path.exists(
            abs_filled
        ):

            raise RuntimeError(
                "BreachDepressions gagal "
                "membuat dem_filled.tif."
            )

        print(
            "[OK] dem_filled.tif"
        )

        # ------------------------------------------------------
        # D8 Pointer
        # ------------------------------------------------------

        print()
        print(
            "[2] D8 Pointer..."
        )

        self.wbt.d8_pointer(
            dem=abs_filled,
            output=abs_flow_dir
        )

        if not os.path.exists(
            abs_flow_dir
        ):

            raise RuntimeError(
                "D8 Pointer gagal "
                "membuat flow_dir.tif."
            )

        print(
            "[OK] flow_dir.tif"
        )

        # ------------------------------------------------------
        # Flow Accumulation
        # ------------------------------------------------------

        print()
        print(
            "[3] D8 Flow Accumulation..."
        )

        self.wbt.d8_flow_accumulation(
            i=abs_filled,
            output=abs_flow_acc,
            out_type="cells"
        )

        if not os.path.exists(
            abs_flow_acc
        ):

            raise RuntimeError(
                "D8 Flow Accumulation gagal "
                "membuat flow_acc.tif."
            )

        print(
            "[OK] flow_acc.tif"
        )

        return (
            abs_filled,
            abs_flow_dir,
            abs_flow_acc
        )

    # ==========================================================
    # WATERSHED DELINEATION
    # ==========================================================

    def delineate_watershed(
        self,
        flow_dir,
        flow_acc,
        lat,
        lon,
        return_edge_status=False
    ):

        base_dir = os.path.abspath(
            "output"
        )

        watershed_raster = os.path.join(
            base_dir,
            "watershed.tif"
        )

        pour_point_shp = os.path.join(
            base_dir,
            "pour_point.shp"
        )

        watershed_polygon_shp = os.path.join(
            base_dir,
            "watershed_poly.shp"
        )

        output_geojson = os.path.join(
            base_dir,
            "watershed.geojson"
        )

        # ------------------------------------------------------
        # Snap outlet ke flow accumulation
        # ------------------------------------------------------

        print()
        print(
            "[WATERSHED] Mencari "
            "cell aliran terdekat..."
        )

        with rasterio.open(
            flow_acc
        ) as src:

            row, col = src.index(
                lon,
                lat
            )

            # Pastikan outlet masih berada
            # dalam raster.
            if (
                row < 0
                or col < 0
                or row >= src.height
                or col >= src.width
            ):

                raise RuntimeError(
                    "Outlet berada di luar "
                    "DEM yang sedang diproses."
                )

            radius = 10

            x0 = max(
                0,
                col - radius
            )

            y0 = max(
                0,
                row - radius
            )

            x1 = min(
                src.width,
                col + radius + 1
            )

            y1 = min(
                src.height,
                row + radius + 1
            )

            width = x1 - x0
            height = y1 - y0

            window = src.read(
                1,
                window=rasterio.windows.Window(
                    x0,
                    y0,
                    width,
                    height
                )
            )

            if window.size > 0:

                valid = np.isfinite(
                    window
                )

                if np.any(valid):

                    safe_window = np.where(
                        valid,
                        window,
                        -np.inf
                    )

                    local_r, local_c = (
                        np.unravel_index(
                            np.argmax(
                                safe_window
                            ),
                            safe_window.shape
                        )
                    )

                    row = y0 + local_r
                    col = x0 + local_c

                    lon, lat = src.xy(
                        row,
                        col
                    )

        print(
            f"[WATERSHED] Outlet snap: "
            f"{lat}, {lon}"
        )

        # ------------------------------------------------------
        # Pour point
        # ------------------------------------------------------

        point = Point(
            lon,
            lat
        )

        gdf_point = gpd.GeoDataFrame(
            geometry=[point],
            crs="EPSG:4326"
        )

        with rasterio.open(
            flow_dir
        ) as raster_src:

            target_crs = (
                raster_src.crs
            )

        if target_crs is None:

            target_crs = "EPSG:4326"

        gdf_point_projected = (
            gdf_point.to_crs(
                target_crs
            )
        )

        # ------------------------------------------------------
        # Hapus pour point lama
        # ------------------------------------------------------

        for ext in [
            ".shp",
            ".shx",
            ".dbf",
            ".prj",
            ".cpg"
        ]:

            p = pour_point_shp.replace(
                ".shp",
                ext
            )

            if os.path.exists(p):

                try:
                    os.remove(p)
                except Exception:
                    pass

        gdf_point_projected.to_file(
            pour_point_shp
        )

        # ------------------------------------------------------
        # Hapus watershed lama
        # ------------------------------------------------------

        if os.path.exists(
            watershed_raster
        ):

            os.remove(
                watershed_raster
            )

        # ------------------------------------------------------
        # Whitebox Watershed
        # ------------------------------------------------------

        print(
            "[WATERSHED] Menjalankan "
            "Whitebox Watershed..."
        )

        self.wbt.watershed(
            d8_pntr=os.path.abspath(
                flow_dir
            ),
            pour_pts=os.path.abspath(
                pour_point_shp
            ),
            output=os.path.abspath(
                watershed_raster
            )
        )

        if not os.path.exists(
            watershed_raster
        ):

            raise RuntimeError(
                "Whitebox gagal membuat "
                "watershed.tif."
            )

        print(
            "[OK] watershed.tif"
        )

        # ------------------------------------------------------
        # Edge validation
        # ------------------------------------------------------

        print(
            "[WATERSHED] Memeriksa "
            "apakah DAS menyentuh edge DEM..."
        )

        with rasterio.open(
            watershed_raster
        ) as src:

            arr = src.read(1)

            mask = (
                arr == 1
            )

            touches_edge = False

            if mask.size > 0:

                touches_edge = bool(
                    np.any(mask[0, :])
                    or np.any(mask[-1, :])
                    or np.any(mask[:, 0])
                    or np.any(mask[:, -1])
                )

        if touches_edge:

            print(
                "⚠ Watershed menyentuh "
                "edge DEM."
            )

        else:

            print(
                "✓ Watershed tidak "
                "menyentuh edge DEM."
            )

        # ------------------------------------------------------
        # Raster → Polygon
        # ------------------------------------------------------

        for ext in [
            ".shp",
            ".shx",
            ".dbf",
            ".prj",
            ".cpg"
        ]:

            p = watershed_polygon_shp.replace(
                ".shp",
                ext
            )

            if os.path.exists(p):

                try:
                    os.remove(p)
                except Exception:
                    pass

        print(
            "[WATERSHED] Mengubah raster "
            "menjadi polygon..."
        )

        self.wbt.raster_to_vector_polygons(
            i=os.path.abspath(
                watershed_raster
            ),
            output=os.path.abspath(
                watershed_polygon_shp
            )
        )

        if not os.path.exists(
            watershed_polygon_shp
        ):

            raise RuntimeError(
                "Gagal membuat "
                "polygon watershed."
            )

        # ------------------------------------------------------
        # Baca polygon
        # ------------------------------------------------------

        gdf_ws = gpd.read_file(
            watershed_polygon_shp
        )

        if "VALUE" in gdf_ws.columns:

            gdf_ws = gdf_ws[
                gdf_ws["VALUE"] == 1
            ]

        elif "val" in gdf_ws.columns:

            gdf_ws = gdf_ws[
                gdf_ws["val"] == 1
            ]

        if gdf_ws.empty:

            raise RuntimeError(
                "Polygon watershed kosong."
            )

        # ------------------------------------------------------
        # Hitung CA
        # ------------------------------------------------------

        print(
            "[WATERSHED] Menghitung CA..."
        )

        # Gunakan UTM berdasarkan longitude
        # outlet, bukan hard-code zone 48/49.
        utm_zone = int(
            (float(lon) + 180) / 6
        ) + 1

        if float(lat) >= 0:

            utm_epsg = (
                32600 + utm_zone
            )

        else:

            utm_epsg = (
                32700 + utm_zone
            )

        gdf_ws_utm = (
            gdf_ws.to_crs(
                epsg=utm_epsg
            )
        )

        total_area_m2 = (
            gdf_ws_utm.geometry.area.sum()
        )

        self.last_area_km2 = (
            total_area_m2
            / 1_000_000
        )

        print()
        print("=" * 60)
        print(
            " LUAS CATCHMENT AREA (CA)"
        )
        print(
            f" {self.last_area_km2:.3f} km²"
        )
        print(
            f" UTM EPSG: {utm_epsg}"
        )
        print("=" * 60)

        # ------------------------------------------------------
        # GeoJSON
        # ------------------------------------------------------

        gdf_ws_wgs84 = (
            gdf_ws.to_crs(
                epsg=4326
            )
        )

        gdf_ws_wgs84.to_file(
            output_geojson,
            driver="GeoJSON"
        )

        print(
            "File GeoJSON berhasil "
            f"disimpan di:"
        )

        print(
            output_geojson
        )

        # ------------------------------------------------------
        # Return
        # ------------------------------------------------------

        if return_edge_status:

            return (
                self.last_area_km2,
                touches_edge
            )

        return self.last_area_km2