from modules.parser.url_parser import URLParser


class QueryBuilder:

    BIG_LAYER = 36

    BIG_SERVER = (
        "https://kspservices.big.go.id/"
        "satupeta/rest/services/"
        "PUBLIK/"
        "SUMBER_DAYA_ALAM_DAN_LINGKUNGAN/"
        "MapServer"
    )

    def build(self, url):

        # ===========================
        # Jika sudah URL BIG
        # ===========================

        if (
            "kspservices.big.go.id" in url
            and "MapServer" in url
            and "query" in url
        ):
            return url

        # ===========================
        # Jika URL BHUMI
        # ===========================

        xmin, ymin, xmax, ymax = URLParser(
            url
        ).bbox()

        return (
            f"{self.BIG_SERVER}/"
            f"{self.BIG_LAYER}/query?"
            f"where=1%3D1"
            f"&geometry={xmin},{ymin},{xmax},{ymax}"
            f"&geometryType=esriGeometryEnvelope"
            f"&inSR=4326"
            f"&spatialRel=esriSpatialRelIntersects"
            f"&outFields=*"
            f"&returnGeometry=true"
            f"&f=geojson"
        )