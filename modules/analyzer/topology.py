import geopandas as gpd
import pandas as pd
from shapely.strtree import STRtree

from modules.analyzer.visibility import VisibilityPredictor
from modules.analyzer.hidden_score import HiddenScore


class TopologyAnalyzer:

    def __init__(self, shp):

        self.gdf = gpd.read_file(shp)

        if self.gdf.crs.is_geographic:
            self.gdf = self.gdf.to_crs(
                self.gdf.estimate_utm_crs()
            )

    def analyze(self):

        print("=" * 70)
        print("TOPOLOGY ANALYZER V5")
        print("=" * 70)

        geometries = list(self.gdf.geometry)
        tree = STRtree(geometries)

        results = []

        total = len(self.gdf)

        for i, row in self.gdf.iterrows():

            original_geom = row.geometry
            geom = original_geom

            # -----------------------------
            # Geometry Health Check
            # -----------------------------
            valid = geom.is_valid
            empty = geom.is_empty
            simple = geom.is_simple

            repaired = False

            if not valid:
                try:
                    fixed = geom.buffer(0)

                    if fixed.is_valid:
                        geom = fixed
                        repaired = True
                except:
                    pass

            nearest = 999999
            touch = 0
            overlap = 0
            inside = False

            candidates = tree.query(geom)

            for idx in candidates:

                if idx == i:
                    continue

                other = geometries[idx]

                if geom.touches(other):
                    touch += 1

                if geom.intersects(other):

                    try:
                        if geom.intersection(other).area > 0:
                            overlap += 1
                    except:
                        pass

                d = geom.distance(other)

                if d < nearest:
                    nearest = d

                if geom.within(other):
                    inside = True

            try:
                compact = (
                    4 * 3.14159265 * geom.area
                ) / (geom.length ** 2)
            except:
                compact = 0

            holes = 0

            if geom.geom_type == "Polygon":
                holes = len(geom.interiors)

            multipart = (
                geom.geom_type == "MultiPolygon"
            )

            island = (
                touch == 0
                and nearest > 0
            )

            results.append({

                "OBJECTID":
                    row.get("OBJECTID", i),

                "AREA_HA":
                    round(geom.area / 10000, 4),

                "VALID":
                    valid,

                "REPAIRED":
                    repaired,

                "EMPTY":
                    empty,

                "SIMPLE":
                    simple,

                "VERTICES":
                    len(geom.exterior.coords),

                "TOUCH":
                    touch,

                "OVERLAP":
                    overlap,

                "INSIDE":
                    inside,

                "NEAREST_M":
                    round(nearest, 2),

                "COMPACT":
                    round(compact, 3),

                "HOLE":
                    holes,

                "MULTIPART":
                    multipart,

                "ISLAND":
                    island,

            })

            print(f"\r{i+1}/{total}", end="")

        print()

        df = pd.DataFrame(results)

        df["HIDDEN_SCORE"] = df.apply(
            HiddenScore.score,
            axis=1
        )

        df["PREDICTION"] = df.apply(
            VisibilityPredictor.predict,
            axis=1
        )

        df = df.sort_values(
            [
                "PREDICTION",
                "HIDDEN_SCORE"
            ],
            ascending=[False, False]
        )

        print(
            df[
                [
                    "OBJECTID",
                    "AREA_HA",
                    "VALID",
                    "REPAIRED",
                    "COMPACT",
                    "HOLE",
                    "ISLAND",
                    "HIDDEN_SCORE",
                    "PREDICTION"
                ]
            ].head(50)
        )

        return df