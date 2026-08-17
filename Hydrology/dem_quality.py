import os
import rasterio
from rasterio.warp import transform_bounds
from shapely.geometry import Point, box


class DEMQualityChecker:
    """
    Pemeriksaan kualitas DEM sebelum analisis hydrology.

    Tidak mengubah file DEM asli.

    Aturan CRS:
    - CRS tersedia       -> gunakan CRS tersebut.
    - CRS kosong + bounds
      terlihat lon/lat   -> dianggap EPSG:4326.
    - CRS kosong + bounds
      tidak masuk akal   -> ERROR.
    """

    def __init__(self, dem_files, outlet=None):
        self.dem_files = dem_files or []
        self.outlet = outlet  # (lat, lon)

    # ==========================================================
    # BOUNDS WGS84
    # ==========================================================

    def _get_bounds_wgs84(self, src):

        if src.crs is None:

            b = src.bounds

            # DEM tanpa CRS tetapi bounds berupa lon/lat
            if (
                -180 <= b.left <= 180
                and -180 <= b.right <= 180
                and -90 <= b.bottom <= 90
                and -90 <= b.top <= 90
            ):
                return box(
                    b.left,
                    b.bottom,
                    b.right,
                    b.top
                )

            return None

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
    # CHECK SINGLE DEM
    # ==========================================================

    def check_dem(self, dem_file):

        result = {
            "file": dem_file,
            "name": os.path.basename(dem_file),
            "exists": False,
            "readable": False,
            "crs": None,
            "effective_crs": None,
            "crs_inferred": False,
            "width": 0,
            "height": 0,
            "resolution_x": None,
            "resolution_y": None,
            "bounds": None,
            "bounds_wgs84": None,
            "nodata": None,
            "min": None,
            "max": None,
            "valid_percent": 0.0,
            "status": "ERROR",
            "warnings": [],
            "errors": []
        }

        # ------------------------------------------------------
        # FILE
        # ------------------------------------------------------

        if not os.path.exists(dem_file):

            result["errors"].append(
                "File tidak ditemukan."
            )

            return result

        result["exists"] = True

        # ------------------------------------------------------
        # OPEN
        # ------------------------------------------------------

        try:

            with rasterio.open(dem_file) as src:

                result["readable"] = True

                result["width"] = src.width
                result["height"] = src.height

                result["crs"] = (
                    str(src.crs)
                    if src.crs
                    else None
                )

                result["resolution_x"] = abs(
                    src.transform.a
                )

                result["resolution_y"] = abs(
                    src.transform.e
                )

                result["bounds"] = {
                    "left": src.bounds.left,
                    "bottom": src.bounds.bottom,
                    "right": src.bounds.right,
                    "top": src.bounds.top
                }

                result["nodata"] = src.nodata

                # --------------------------------------------------
                # CRS
                # --------------------------------------------------

                if src.crs is not None:

                    result["effective_crs"] = (
                        str(src.crs)
                    )

                else:

                    b = src.bounds

                    geographic_bounds = (
                        -180 <= b.left <= 180
                        and -180 <= b.right <= 180
                        and -90 <= b.bottom <= 90
                        and -90 <= b.top <= 90
                    )

                    if geographic_bounds:

                        result[
                            "effective_crs"
                        ] = "EPSG:4326"

                        result[
                            "crs_inferred"
                        ] = True

                    else:

                        result["errors"].append(
                            "CRS kosong dan bounds "
                            "tidak terlihat seperti "
                            "koordinat geografis."
                        )

                # --------------------------------------------------
                # RESOLUTION
                # --------------------------------------------------

                if (
                    result["resolution_x"] <= 0
                    or result["resolution_y"] <= 0
                ):

                    result["errors"].append(
                        "Resolusi raster tidak valid."
                    )

                # --------------------------------------------------
                # SIZE
                # --------------------------------------------------

                if (
                    src.width <= 0
                    or src.height <= 0
                ):

                    result["errors"].append(
                        "Ukuran raster tidak valid."
                    )

                # --------------------------------------------------
                # BOUNDS WGS84
                # --------------------------------------------------

                bounds_wgs84 = (
                    self._get_bounds_wgs84(src)
                )

                if bounds_wgs84 is not None:

                    result["bounds_wgs84"] = {
                        "left": bounds_wgs84.bounds[0],
                        "bottom": bounds_wgs84.bounds[1],
                        "right": bounds_wgs84.bounds[2],
                        "top": bounds_wgs84.bounds[3]
                    }

                else:

                    result["errors"].append(
                        "Coverage geografis "
                        "tidak dapat ditentukan."
                    )

                # --------------------------------------------------
                # SAMPLE DATA
                # --------------------------------------------------

                sample_height = min(
                    src.height,
                    1000
                )

                sample_width = min(
                    src.width,
                    1000
                )

                sample = src.read(
                    1,
                    out_shape=(
                        sample_height,
                        sample_width
                    )
                )

                import numpy as np

                data = sample.astype(
                    "float64"
                )

                invalid = ~np.isfinite(
                    data
                )

                if src.nodata is not None:

                    invalid |= np.isclose(
                        data,
                        src.nodata,
                        equal_nan=True
                    )

                valid = data[~invalid]

                total = data.size

                if total > 0:

                    result[
                        "valid_percent"
                    ] = (
                        len(valid)
                        / total
                    ) * 100.0

                if len(valid) > 0:

                    result["min"] = float(
                        valid.min()
                    )

                    result["max"] = float(
                        valid.max()
                    )

                else:

                    result["errors"].append(
                        "Tidak ada pixel DEM valid."
                    )

                # --------------------------------------------------
                # ELEVATION SANITY
                # --------------------------------------------------

                if result["min"] is not None:

                    if result["min"] < -500:

                        result["warnings"].append(
                            "Elevasi minimum sangat rendah: "
                            f"{result['min']:.2f} m"
                        )

                if result["max"] is not None:

                    if result["max"] > 10000:

                        result["warnings"].append(
                            "Elevasi maksimum sangat tinggi: "
                            f"{result['max']:.2f} m"
                        )

                # --------------------------------------------------
                # VALID PIXEL
                # --------------------------------------------------

                if result["valid_percent"] < 90:

                    result["warnings"].append(
                        "Pixel valid kurang dari 90%."
                    )

                # --------------------------------------------------
                # CRS INFERRED
                # --------------------------------------------------

                if result["crs_inferred"]:

                    result["warnings"].append(
                        "CRS metadata kosong; "
                        "EPSG:4326 diinferensikan "
                        "dari bounds."
                    )

                # --------------------------------------------------
                # FINAL STATUS
                # --------------------------------------------------

                if result["errors"]:

                    result["status"] = "ERROR"

                else:

                    # CRS inferred bukan error.
                    # DEM tetap siap dipakai.
                    result["status"] = "OK"

        except Exception as e:

            result["errors"].append(
                f"Gagal membaca DEM: {e}"
            )

            result["status"] = "ERROR"

        return result

    # ==========================================================
    # CHECK ALL
    # ==========================================================

    def check_all(self):

        results = []

        print()
        print("=" * 70)
        print("DEM QUALITY CHECK")
        print("=" * 70)

        print(
            f"Jumlah DEM yang diperiksa : "
            f"{len(self.dem_files)}"
        )

        for dem in self.dem_files:

            print()
            print(
                f"[CHECK] "
                f"{os.path.basename(dem)}"
            )

            result = self.check_dem(dem)

            results.append(result)

            print(
                f"  STATUS : "
                f"{result['status']}"
            )

            print(
                f"  CRS    : "
                f"{result['crs'] or 'NONE'}"
            )

            print(
                f"  EFFECTIVE CRS : "
                f"{result['effective_crs'] or 'UNKNOWN'}"
            )

            if result["crs_inferred"]:

                print(
                    "  CRS MODE : "
                    "AUTO-INFERRED"
                )

            print(
                f"  RES    : "
                f"{result['resolution_x']:.6f} x "
                f"{result['resolution_y']:.6f}"
            )

            if result["min"] is not None:

                print(
                    f"  ELEV   : "
                    f"{result['min']:.2f} - "
                    f"{result['max']:.2f} m"
                )

            print(
                f"  VALID  : "
                f"{result['valid_percent']:.2f}%"
            )

            for warning in result["warnings"]:

                print(
                    f"  WARNING: {warning}"
                )

            for error in result["errors"]:

                print(
                    f"  ERROR  : {error}"
                )

        return results

    # ==========================================================
    # OUTLET COVERAGE
    # ==========================================================

    def check_outlet_coverage(
        self,
        results
    ):

        if self.outlet is None:

            return {
                "covered": False,
                "covering_dems": [],
                "message": "Outlet belum ditentukan."
            }

        lat, lon = self.outlet

        outlet_point = Point(
            float(lon),
            float(lat)
        )

        covering = []

        for result in results:

            bounds = result.get(
                "bounds_wgs84"
            )

            if not bounds:
                continue

            dem_box = box(
                bounds["left"],
                bounds["bottom"],
                bounds["right"],
                bounds["top"]
            )

            if dem_box.covers(
                outlet_point
            ):

                covering.append(
                    result["file"]
                )

        covered = bool(
            covering
        )

        if covered:

            message = (
                f"Outlet berada dalam "
                f"coverage {len(covering)} DEM."
            )

        else:

            message = (
                "Outlet berada di luar "
                "seluruh DEM."
            )

        print()
        print("=" * 70)
        print("OUTLET COVERAGE CHECK")
        print("=" * 70)

        print(
            f"Outlet : {lat}, {lon}"
        )

        print(
            f"Status : {message}"
        )

        for dem in covering:

            print(
                f"  [COVER] "
                f"{os.path.basename(dem)}"
            )

        return {
            "covered": covered,
            "covering_dems": covering,
            "message": message
        }

    # ==========================================================
    # OVERLAP
    # ==========================================================

    def check_overlap(
        self,
        results
    ):

        print()
        print("=" * 70)
        print("DEM OVERLAP CHECK")
        print("=" * 70)

        valid = []

        for result in results:

            bounds = result.get(
                "bounds_wgs84"
            )

            if bounds:

                valid.append(
                    (
                        result["file"],
                        box(
                            bounds["left"],
                            bounds["bottom"],
                            bounds["right"],
                            bounds["top"]
                        )
                    )
                )

        overlaps = []

        for i in range(
            len(valid)
        ):

            file_a, box_a = valid[i]

            for j in range(
                i + 1,
                len(valid)
            ):

                file_b, box_b = valid[j]

                if box_a.intersects(
                    box_b
                ):

                    intersection = (
                        box_a.intersection(
                            box_b
                        )
                    )

                    if not intersection.is_empty:

                        overlaps.append(
                            (
                                file_a,
                                file_b,
                                intersection.area
                            )
                        )

        if not overlaps:

            print(
                "Tidak ditemukan overlap DEM."
            )

        else:

            print(
                f"Ditemukan "
                f"{len(overlaps)} pasangan "
                f"DEM yang overlap."
            )

            for a, b, area in overlaps:

                print(
                    f"  OVERLAP: "
                    f"{os.path.basename(a)} <-> "
                    f"{os.path.basename(b)}"
                )

        return overlaps

    # ==========================================================
    # RUN
    # ==========================================================

    def run(self):

        results = self.check_all()

        outlet_result = (
            self.check_outlet_coverage(
                results
            )
        )

        overlaps = (
            self.check_overlap(
                results
            )
        )

        errors = [
            r for r in results
            if r["status"] == "ERROR"
        ]

        warnings = [
            r for r in results
            if r["warnings"]
        ]

        print()
        print("=" * 70)
        print("DEM QUALITY SUMMARY")
        print("=" * 70)

        print(
            f"Total DEM       : "
            f"{len(results)}"
        )

        print(
            f"OK              : "
            f"{len(results) - len(errors)}"
        )

        print(
            f"WARNING         : "
            f"{len(warnings)}"
        )

        print(
            f"ERROR           : "
            f"{len(errors)}"
        )

        print(
            f"Outlet covered  : "
            f"{'YES' if outlet_result['covered'] else 'NO'}"
        )

        print(
            f"Overlap pairs    : "
            f"{len(overlaps)}"
        )

        ready = (
            len(errors) == 0
            and outlet_result["covered"]
        )

        print(
            f"READY           : "
            f"{'YES' if ready else 'NO'}"
        )

        print("=" * 70)

        return {
            "results": results,
            "outlet": outlet_result,
            "overlaps": overlaps,
            "errors": errors,
            "warnings": warnings,
            "ready": ready
        }