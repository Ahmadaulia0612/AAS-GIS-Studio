import os
import shapefile


class SHPExporter:

    def export(self, geojson, filename):

        os.makedirs("output", exist_ok=True)

        path = os.path.join("output", filename)

        writer = shapefile.Writer(
            path,
            shapeType=shapefile.POLYGON
        )

        # ==========================
        # Field
        # ==========================

        props = geojson["features"][0]["properties"]

        fields = []

        for key, value in props.items():

            field = key[:10].upper()

            fields.append(key)

            if isinstance(value, int):

                writer.field(field, "N")

            elif isinstance(value, float):

                writer.field(field, "F", decimal=8)

            else:

                writer.field(field, "C", size=254)

        # ==========================
        # Geometry
        # ==========================

        for feature in geojson["features"]:

            geom = feature["geometry"]

            if geom["type"] == "Polygon":

                writer.poly(geom["coordinates"])

            elif geom["type"] == "MultiPolygon":

                parts = []

                for poly in geom["coordinates"]:
                    parts.extend(poly)

                writer.poly(parts)

            else:
                continue

            writer.record(
                *[
                    feature["properties"].get(f)
                    for f in fields
                ]
            )

        writer.close()

        # ==========================
        # PRJ
        # ==========================

        with open(path + ".prj", "w") as prj:

            prj.write(
                'GEOGCS["WGS 84",'
                'DATUM["WGS_1984",'
                'SPHEROID["WGS 84",6378137,298.257223563]],'
                'PRIMEM["Greenwich",0],'
                'UNIT["Degree",0.0174532925199433]]'
            )

        return path + ".shp"