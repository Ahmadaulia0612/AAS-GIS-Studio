from modules.downloader.big_downloader import BIGDownloader
from modules.downloader.query_builder import QueryBuilder

url = input("Paste URL BIG atau BHUMI:\n")

if "bhumi" in url:
    url = QueryBuilder().build(url)

geojson = BIGDownloader().download(url)

print("Total feature:", len(geojson["features"]))

for i, feature in enumerate(geojson["features"]):
    try:
        geom = feature["geometry"]

        if geom is None:
            print(f"{i}: geometry = None")
            continue

        print(
            i,
            geom["type"],
            len(geom.get("coordinates", []))
        )

    except Exception as e:
        print(f"{i}: ERROR -> {e}")