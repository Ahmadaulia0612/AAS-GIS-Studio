import math


class GeometryTools:

    @staticmethod
    def area_ha(geom):
        return geom.area / 10000

    @staticmethod
    def perimeter(geom):
        return geom.length

    @staticmethod
    def vertex_count(geom):
        if geom.geom_type == "Polygon":
            return len(geom.exterior.coords)

        elif geom.geom_type == "MultiPolygon":
            total = 0
            for p in geom.geoms:
                total += len(p.exterior.coords)
            return total

        return 0

    @staticmethod
    def compactness(geom):

        if geom.length == 0:
            return 0

        return (4 * math.pi * geom.area) / (geom.length ** 2)

    @staticmethod
    def aspect_ratio(geom):

        minx, miny, maxx, maxy = geom.bounds

        width = maxx - minx
        height = maxy - miny

        if height == 0:
            return 0

        return width / height