from modules.downloader.query_builder import QueryBuilder

url = input("URL BHUMI : ")

query = QueryBuilder().build(url)

print()
print(query)