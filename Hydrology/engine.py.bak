import os
import geopandas as gpd
import rasterio
from shapely.geometry import Point
import numpy as np

from Hydrology.dem_merge import DEMMerger
import whitebox

class HydrologyEngine:
    def __init__(self, dem_files, river_file, outlet):
        self.dem_files = dem_files
        self.river_file = river_file
        self.outlet = outlet  # (lat, lon)
        
        self.wbt = whitebox.WhiteboxTools()
        self.wbt.set_verbose_mode(False)
        
        os.makedirs("output", exist_ok=True)
        self.merged_dem = os.path.abspath("output/merged_dem.tif")
        self.last_area_km2 = 0.0

    def run(self):
        print("=" * 60)
        print("MENJALANKAN HYDROLOGY ENGINE (STABLE MERGE & DELINEATION)")
        print("=" * 60)

        # 1. Merge DEM secara utuh dari daftar file yang dimuat
        print("\n[1/3] Menggabungkan file DEM...")
        merger = DEMMerger(dem_files=self.dem_files)
        self.merged_dem = merger.merge(output_path="output/merged_dem.tif")

        # 2. Analisis Hidrologi Terrain (Fill Sink, Flow Direction, Flow Accumulation)
        print("\n[2/3] Analisis Hidrologi Terrain...")
        dem_filled, flow_dir, flow_acc = self.run_hydrology_steps(self.merged_dem)

        # 3. Delineasi Watershed
        print("\n[3/3] Delineasi Watershed...")
        lat, lon = self.outlet
        self.delineate_watershed(flow_dir, flow_acc, lat, lon)

        print("PROSES HIDROLOGI SELESAI SEMPURNA!")

    def run_hydrology_steps(self, dem_input):
        base_dir = os.path.abspath("output")
        dem_filled = os.path.join(base_dir, "dem_filled.tif")
        flow_dir = os.path.join(base_dir, "flow_dir.tif")
        flow_acc = os.path.join(base_dir, "flow_acc.tif")
        normalized_dem = os.path.join(base_dir, "dem_normalized.tif")

        for f in [dem_filled, flow_dir, flow_acc, normalized_dem]:
            if os.path.exists(f):
                os.remove(f)

        abs_dem = os.path.abspath(dem_input)

        with rasterio.open(abs_dem) as src:
            data = src.read(1)
            transform = src.transform
            profile = {
                'driver': 'GTiff',
                'height': src.height,
                'width': src.width,
                'count': 1,
                'dtype': 'float32',
                'crs': src.crs if src.crs else 'EPSG:4326', 
                'transform': transform,
                'compress': 'lzw'
            }
            with rasterio.open(normalized_dem, "w", **profile) as dst:
                dst.write(data.astype("float32"), 1)

        target_dem = normalized_dem if os.path.exists(normalized_dem) else abs_dem

        # Fill Sink (Breach Depressions)
        self.wbt.breach_depressions(dem=target_dem, output=dem_filled)

        # Flow Direction (D8 Pointer)
        self.wbt.d8_pointer(dem=dem_filled, output=flow_dir)

        # Flow Accumulation
        self.wbt.d8_flow_accumulation(i=dem_filled, output=flow_acc, out_type="cells")

        return dem_filled, flow_dir, flow_acc

    def delineate_watershed(self, flow_dir, flow_acc, lat, lon):
        base_dir = os.path.abspath("output")
        watershed_raster = os.path.join(base_dir, "watershed.tif")
        pour_point_shp = os.path.join(base_dir, "pour_point.shp")
        watershed_polygon_shp = os.path.join(base_dir, "watershed_poly.shp")
        output_geojson = os.path.join(base_dir, "watershed.geojson")

        with rasterio.open(flow_acc) as src:
            row, col = src.index(lon, lat)
            # Ambil jendela pencarian piksel terdekat dengan akumulasi aliran tertinggi
            window = src.read(1, window=rasterio.windows.Window(max(0, col - 10), max(0, row - 10), 20, 20))
            if window.size > 0:
                local_r, local_c = np.unravel_index(np.argmax(window), window.shape)
                row = max(0, row - 10) + local_r
                col = max(0, col - 10) + local_c
                lon, lat = src.xy(row, col)

        point = Point(lon, lat)
        gdf_point = gpd.GeoDataFrame(geometry=[point], crs="EPSG:4326")
        
        with rasterio.open(flow_dir) as raster_src:
            target_crs = raster_src.crs
            
        gdf_point_projected = gdf_point.to_crs(target_crs)
        
        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
            p = pour_point_shp.replace('.shp', ext)
            if os.path.exists(p):
                os.remove(p)

        gdf_point_projected.to_file(pour_point_shp)

        # Proses Watershed dari WhiteboxTools
        self.wbt.watershed(
            d8_pntr=flow_dir,
            pour_pts=pour_point_shp,
            output=watershed_raster
        )

        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
            p = watershed_polygon_shp.replace('.shp', ext)
            if os.path.exists(p):
                os.remove(p)

        self.wbt.raster_to_vector_polygons(
            i=watershed_raster,
            output=watershed_polygon_shp
        )

        if not os.path.exists(watershed_polygon_shp):
            print("Error: Gagal membuat poligon watershed.")
            return

        gdf_ws = gpd.read_file(watershed_polygon_shp)

        if "VALUE" in gdf_ws.columns:
            gdf_ws = gdf_ws[gdf_ws["VALUE"] == 1]
        elif "val" in gdf_ws.columns:
            gdf_ws = gdf_ws[gdf_ws["val"] == 1]

        if gdf_ws.empty:
            print("Peringatan: Poligon watershed kosong!")
            return

        # Hitung luas dalam UTM (Zone 49N / 48N otomatis sesuai CRS)
        gdf_ws_utm = gdf_ws.to_crs(epsg=32749) if target_crs and "327" in str(target_crs) else gdf_ws.to_crs(epsg=32748)
        total_area_m2 = gdf_ws_utm.geometry.area.sum()
        self.last_area_km2 = total_area_m2 / 1_000_000
        
        print(f"==================================================")
        print(f" LUAS CATCHMENT AREA (CA) : {self.last_area_km2:.3f} km²")
        print(f"==================================================")

        gdf_ws_wgs84 = gdf_ws.to_crs(epsg=4326)
        gdf_ws_wgs84.to_file(output_geojson, driver="GeoJSON")
        print(f"File GeoJSON berhasil disimpan di: {output_geojson}")
        
        return self.last_area_km2