import math


class FeatureEngineering:

    @staticmethod
    def compactness(geom):

        if geom.area == 0:
            return 0

        return (
            4 * math.pi * geom.area
        ) / (geom.length ** 2)

    @staticmethod
    def convexity(geom):

        hull = geom.convex_hull

        if hull.area == 0:
            return 0

        return geom.area / hull.area

    @staticmethod
    def rectangularity(geom):

        rect = geom.minimum_rotated_rectangle

        if rect.area == 0:
            return 0

        return geom.area / rect.area

    @staticmethod
    def elongation(geom):

        rect = geom.minimum_rotated_rectangle

        coords = list(rect.exterior.coords)

        edges = []

        for i in range(4):

            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]

            edges.append(
                math.hypot(x2 - x1, y2 - y1)
            )

        edges.sort()

        short = edges[0]
        long = edges[-1]

        if long == 0:
            return 0

        return short / long