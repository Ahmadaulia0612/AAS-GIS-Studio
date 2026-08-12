import os
import geopandas as gpd

def export_watershed_to_kml(geojson_path="output/watershed.geojson", kml_output_path="output/watershed.kml"):
    """Mengekspor file GeoJSON watershed ke format KML untuk Google Earth"""
    try:
        if not os.path.exists(geojson_path):
            raise Exception("File watershed GeoJSON belum tersedia. Jalankan Watershed terlebih dahulu.")
        
        gdf = gpd.read_file(geojson_path)
        
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)
            
        gdf.to_file(kml_output_path, driver='KML')
        return kml_output_path
    except Exception as e:
        raise Exception(f"Gagal ekspor KML: {str(e)}")


def export_candidates_to_geojson(candidates, output_path="output/candidates.geojson"):
    """Mengekspor titik kandidat hydropower ke GeoJSON"""
    try:
        from shapely.geometry import Point
        import pandas as pd

        if not candidates:
            gdf = gpd.GeoDataFrame(columns=['geometry'], crs="EPSG:4326")
        else:
            records = []
            for c in candidates:
                pt = Point(c['lon'], c['lat'])
                records.append({
                    'id': c.get('id', 0),
                    'head_m': c.get('head_m', 0),
                    'flow_m3s': c.get('flow_m3s', 0),
                    'power_mw': c.get('power_mw', 0),
                    'geometry': pt
                })
            gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        gdf.to_file(output_path, driver="GeoJSON")
    except Exception as e:
        print(f"Gagal ekspor candidates GeoJSON: {e}")