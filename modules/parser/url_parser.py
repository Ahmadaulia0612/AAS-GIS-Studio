from urllib.parse import urlparse, parse_qs


class URLParser:

    def __init__(self, url: str):
        self.url = url

    def bbox(self):

        query = parse_qs(
            urlparse(self.url).query
        )

        if "bbox" not in query:
            raise Exception("URL BHUMI tidak memiliki bbox")

        bbox = query["bbox"][0].split(",")

        return (
            float(bbox[0]),
            float(bbox[1]),
            float(bbox[2]),
            float(bbox[3]),
        )