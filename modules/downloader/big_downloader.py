import requests


class BIGDownloader:

    def download(self, url):

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, headers=headers, timeout=30)

        r.raise_for_status()

        data = r.json()

        if "features" not in data:
            raise Exception("GeoJSON tidak memiliki 'features'")

        return data