import os
import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon

from Hydrology.screening import ScreeningEngine
from Hydrology.power import PowerCalculator
from Hydrology.debit import DischargeCalculator
from Hydrology.terrain import TerrainAnalyzer
from Hydrology.hydrology import HydrologyAnalyzer
from Hydrology.config import SAMPLING_DISTANCE, WEIR_HEIGHT
from Hydrology.cluster import filter_close_candidates

class RiverScanner:
    def __init__(self, river_path, dem_path, flow_acc_path, penstock_length_m=1500):
        self.river_path = river_path
        self.dem_path = dem_path
        self.flow_acc_path = flow_acc_path
        self.penstock_length_m = penstock_length_m
        
        self.screening_engine = ScreeningEngine()
        self.power_calc = PowerCalculator()
        self.debit_calc = DischargeCalculator()

    def scan(self, target_mw=0.0, progress_callback=None):
        self.screening_engine.clear()
        
        if not os.path.exists(self.river_path):
            print(f"File sungai tidak ditemukan: {self.river_path}")
            return []

        try:
            gdf_river = gpd.read_file(self.river_path, layer='_Hidrografi_50K_SUNGAI_LN_50K')
        except Exception:
            gdf_river = gpd.read_file(self.river_path)

        if gdf_river.crs is None or gdf_river.crs.to_epsg() != 4326:
            gdf_river = gdf_river.to_crs(epsg=4326)

        total_features = len(gdf_river)
        print(f"Jumlah segmen sungai dimuat: {total_features}")
        print("Membuka file DEM & Flow Accumulation ke RAM...")
        
        terrain = TerrainAnalyzer(self.dem_path)
        hydrology = HydrologyAnalyzer(self.flow_acc_path)
        print("Berhasil! Memulai pemindaian...")

        step_degrees = SAMPLING_DISTANCE / 111000.0  
        penstock_degrees = self.penstock_length_m / 111000.0

        for idx, row in gdf_river.iterrows():
            if idx % 5000 == 0 and idx > 0:
                print(f"Progress: {idx} dari {total_features} segmen...")

            geom = row.geometry
            if geom is None or geom.is_empty:
                continue

            lines = []
            if isinstance(geom, LineString):
                lines.append(geom)
            elif isinstance(geom, MultiLineString):
                lines.extend(list(geom.geoms))
            elif isinstance(geom, Polygon):
                lines.append(geom.exterior)
            elif isinstance(geom, MultiPolygon):
                for p in geom.geoms:
                    lines.append(p.exterior)

            for line in lines:
                length = line.length
                if length <= 0 or step_degrees <= 0:
                    continue

                distances = np.arange(0, length, step_degrees)

                for current_dist in distances:
                    p_intake = line.interpolate(current_dist)
                    lon_intake, lat_intake = p_intake.x, p_intake.y
                    
                    ca = hydrology.get_catchment_area(lon_intake, lat_intake)
                    
                    if ca >= 5.0:
                        target_dist_ph = min(current_dist + penstock_degrees, length)
                        p_ph = line.interpolate(target_dist_ph)
                        
                        z_intake = terrain.get_elevation(lon_intake, lat_intake)
                        z_ph = terrain.get_elevation(p_ph.x, p_ph.y)
                        
                        if z_intake is not None and z_ph is not None:
                            gross_head = z_intake - z_ph
                            
                            if gross_head > 5.0:
                                discharge = self.debit_calc.calculate(ca)
                                power = self.power_calc.calculate(discharge, gross_head, WEIR_HEIGHT)
                                
                                self.screening_engine.add(
                                    lat=lat_intake,
                                    lon=lon_intake,
                                    catchment_area=ca,
                                    head=gross_head,
                                    discharge=discharge,
                                    power=power
                                )

            if progress_callback and total_features > 0:
                progress_callback(int(((idx + 1) / total_features) * 100))

        terrain.close()
        hydrology.close()
        
        # Lakukan ranking berdasarkan power terbesar
        self.screening_engine.ranking()
        
        # Terapkan fungsi kluster untuk menyaring titik yang jaraknya < 1000 meter
        self.screening_engine.candidates = filter_close_candidates(
            self.screening_engine.candidates, 
            min_distance_m=1000
        )
        
        # Logika Otomatis: Jika ada target_mw, coba filter
        if target_mw > 0:
            filtered_candidates = self.screening_engine.filter(target_mw)
            # Jika hasil filter kosong karena tidak ada yang mencapai target, 
            # ambil otomatis 10 kandidat terbaik teratas sebagai alternatif
            if not filtered_candidates and self.screening_engine.candidates:
                print(f"Peringatan: Tidak ada titik yang mencapai target {target_mw} MW.")
                print("Menampilkan otomatis 10 titik potensi terbaik teratas di wilayah ini...")
                return self.screening_engine.candidates[:10]
            return filtered_candidates
            
        return self.screening_engine.candidates