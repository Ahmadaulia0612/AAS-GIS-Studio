from modules.downloader.query_builder import QueryBuilder
from modules.downloader.big_downloader import BIGDownloader

bhumi = input("URL BHUMI : ")

query = QueryBuilder().build(bhumi)

print("\nQuery BIG:")
print(query)

geojson = BIGDownloader().download(query)

print("\nType :", geojson["type"])
print("Jumlah Feature :", len(geojson["features"]))