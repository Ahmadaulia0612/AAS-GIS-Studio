import os
from Hydrology.dem_merge import DEMMerger

class HydrologyEngine:
    def __init__(self, dem_files, river_file, outlet):
        self.dem_files = dem_files
        self.river_file = river_file
        self.outlet = outlet  # Format: (lat, lon) dari klik peta
        self.merged_dem = None

    def run(self):
        print("=" * 60)
        print("MEMULAI PROSES DELINEASI CATCHMENT AREA (CA)")
        print("=" * 60)
        
        if not self.outlet:
            print("Error: Outlet belum dipilih pada peta!")
            return

        lat, lon = self.outlet
        print(f"Koordinat Outlet Dipilih : Lat {lat}, Lon {lon}")
        print(f"File Sungai (River)      : {self.river_file}")
        print(f"Jumlah Tile DEM          : {len(self.dem_files)}")
        
        # ---------------------------------------------------------
        # TAHAPAN PROSES HIDROLOGI
        # ---------------------------------------------------------
        # 1. Pemrosesan DEM (Merge / Mosaic menggunakan DEMMerger)
        self.process_terrain()
        
        # 2. Snap Outlet ke jaringan sungai terdekat
        self.snap_outlet()
        
        # 3. Delineasi Catchment Area & Hitung Luas Basin
        self.delineate_watershed()
        
        print("=" * 60)
        print("Proses hidrologi dan delineasi selesai!")
        print("=" * 60)

    def process_terrain(self):
        print("[1/3] Memproses Terrain DEM (Merging/Mosaic)...")
        try:
            merger = DEMMerger()
            self.merged_dem = merger.merge(self.dem_files)
            print(f"DEM Berhasil digabung ke: {self.merged_dem}")
        except Exception as e:
            print(f"Error saat merging DEM: {e}")

    def snap_outlet(self):
        print("[2/3] Melakukan Snap Outlet ke garis sungai terdekat...")
        # Logika snap outlet berdasarkan koordinat klik (lat, lon) dan file sungai
        pass

    def delineate_watershed(self):
        print("[3/3] Menghitung batas Catchment Area dan luas basin...")
        # Logika delineasi watershed menggunakan DEM hasil merge dan outlet
        pass