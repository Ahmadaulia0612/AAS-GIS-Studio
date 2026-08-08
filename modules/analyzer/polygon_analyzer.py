from pathlib import Path
import math
import geopandas as gpd


class PolygonAnalyzer:

    def analyze(self, shp_path):

        gdf = gpd.read_file(shp_path)

        # ==========================
        # Ubah ke UTM
        # ==========================

        gdf = gdf.to_crs(gdf.estimate_utm_crs())

        # ==========================
        # Perbaiki geometri
        # ==========================

        gdf["geometry"] = gdf.geometry.buffer(0)

        # ==========================
        # AREA
        # ==========================

        gdf["AREA_HA"] = gdf.geometry.area.abs() / 10000

        # ==========================
        # PERIMETER
        # ==========================

        gdf["PERIMETER"] = gdf.geometry.length

        # ==========================
        # VERTEX
        # ==========================

        def vertex_count(g):

            if g.geom_type == "Polygon":
                return len(g.exterior.coords)

            elif g.geom_type == "MultiPolygon":
                return sum(len(p.exterior.coords) for p in g.geoms)

            return 0

        gdf["VERTICES"] = gdf.geometry.apply(vertex_count)

        # ==========================
        # COMPACTNESS
        # ==========================

        def compactness(g):

            if g.length == 0:
                return 0

            return (4 * math.pi * g.area) / (g.length ** 2)

        gdf["COMPACT"] = gdf.geometry.apply(compactness)

        # ==========================
        # ASPECT RATIO
        # ==========================

        def aspect(g):

            minx, miny, maxx, maxy = g.bounds

            width = maxx - minx
            height = maxy - miny

            if height == 0:
                return 0

            return width / height

        gdf["ASPECT"] = gdf.geometry.apply(aspect)

        # ==========================
        # HOLE
        # ==========================

        def has_hole(g):

            if g.geom_type == "Polygon":
                return len(g.interiors) > 0

            return False

        gdf["HOLE"] = gdf.geometry.apply(has_hole)

        # ==========================
        # MULTIPART
        # ==========================

        gdf["MULTIPART"] = gdf.geometry.geom_type == "MultiPolygon"

        # ==========================
        # VALID
        # ==========================

        gdf["VALID"] = gdf.geometry.is_valid

        # ==========================
        # REPORT
        # ==========================

        print("=" * 70)
        print("POLYGON ANALYZER V2")
        print("=" * 70)

        print(f"Total Feature : {len(gdf)}")
        print(f"Total Area    : {gdf['AREA_HA'].sum():.2f} Ha")
        print(f"Min Area      : {gdf['AREA_HA'].min():.4f} Ha")
        print(f"Max Area      : {gdf['AREA_HA'].max():.4f} Ha")
        print()

        print(
            gdf[
                [
                    "AREA_HA",
                    "PERIMETER",
                    "VERTICES",
                    "COMPACT",
                    "ASPECT",
                    "HOLE",
                    "MULTIPART",
                    "VALID",
                ]
            ]
            .sort_values("AREA_HA", ascending=False)
            .head(20)
        )

        return gdf