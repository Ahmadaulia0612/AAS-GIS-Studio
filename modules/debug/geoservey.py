import requests
from urllib.parse import urlparse, parse_qs, urlencode
from copy import deepcopy


class GeoServerInspector:

    def __init__(self, verify=False):
        self.verify = verify

    def inspect(self, getmap_url):

        parsed = urlparse(getmap_url)

        params = {
            k.upper(): v[0]
            for k, v in parse_qs(parsed.query).items()
        }

        print("=" * 80)
        print("ORIGINAL")
        print("=" * 80)

        for k, v in params.items():
            print(f"{k} = {v}")

        print()

        self.test(parsed, params)

    def test(self, parsed, params):

        tests = [

            "GetCapabilities",
            "DescribeLayer",
            "GetLegendGraphic",
            "GetFeatureInfo"

        ]

        for request_name in tests:

            p = deepcopy(params)

            p["REQUEST"] = request_name

            url = (
                parsed.scheme
                + "://"
                + parsed.netloc
                + parsed.path
                + "?"
                + urlencode(p)
            )

            print("=" * 80)
            print(request_name)
            print("=" * 80)

            try:

                r = requests.get(
                    url,
                    timeout=30,
                    verify=self.verify
                )

                print("STATUS :", r.status_code)
                print("TYPE   :", r.headers.get("Content-Type"))
                print(r.text[:1000])

            except Exception as e:

                print(e)

            print()