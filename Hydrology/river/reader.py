import geopandas as gpd
import pandas as pd
import fiona

class RiverReader:
    """Kelas untuk membaca dan menggabungkan seluruh layer sungai dari GeoPackage / Shapefile"""
    
    def load(self, filename):
        try:
            river_ln = None
            river_ar = None

            if filename.endswith('.gpkg'):
                layers = fiona.listlayers(filename)
                line_layers = [l for l in layers if 'ln' in l.lower() or 'line' in l.lower() or 'sungai' in l.lower() or 'garis' in l.lower()]
                
                target_layers = line_layers if line_layers else layers
                
                gdfs = []
                for lyr in target_layers:
                    try:
                        temp_gdf = gpd.read_file(filename, layer=lyr)
                        if not temp_gdf.empty and any(temp_gdf.geometry.geom_type.str.contains('Line', case=False, na=False)):
                            gdfs.append(temp_gdf)
                    except Exception:
                        continue
                
                if gdfs:
                    river_ln = pd.concat(gdfs, ignore_index=True)
                else:
                    river_ln = gpd.read_file(filename, layer=layers[0])
            else:
                river_ln = gpd.read_file(filename)

            # Konversi ke EPSG:4326 agar sesuai dengan peta web Leaflet
            if river_ln is not None and not river_ln.empty:
                if river_ln.crs is None:
                    river_ln = river_ln.set_crs(epsg=4326, allow_override=True)
                elif river_ln.crs.to_epsg() != 4326:
                    river_ln = river_ln.to_crs(epsg=4326)

            return river_ln, river_ar

        except Exception as e:
            raise Exception(f"Gagal membaca file River: {str(e)}")