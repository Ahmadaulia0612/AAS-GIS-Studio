from modules.downloader.query_builder import QueryBuilder
from modules.downloader.big_downloader import BIGDownloader
from modules.exporter.shp_exporter import SHPExporter


bhumi = input("URL BHUMI : ")

query = QueryBuilder().build(bhumi)

geojson = BIGDownloader().download(query)

print("Feature :", len(geojson["features"]))

file = SHPExporter().export(
    geojson,
    "area_baku_sawah"
)

print()
print("SHP BERHASIL")
print(file)