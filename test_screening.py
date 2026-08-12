import os
import time
from Hydrology.scanner import RiverScanner

RIVER_FILE = r"D:\Kalbar\tes_rbi\Bengkayang Coba.gpkg"
DEM_FILE = r"output/merged_dem.tif"
FLOW_ACC_FILE = "output/flow_acc.tif"

def main():
    print("=" * 60)
    print("TESTING FAST AUTO SCANNING ENGINE (HYDROPOWER SCREENING)")
    print("=" * 60)

    start_time = time.time()

    scanner = RiverScanner(
        river_path=RIVER_FILE,
        dem_path=DEM_FILE,
        flow_acc_path=FLOW_ACC_FILE,
        penstock_length_m=1500
    )

    print("\nSedang memindai jaringan sungai Bengkayang...")
    TARGET_MW = 0.0  # Target daya minimal
    candidates = scanner.scan(target_mw=TARGET_MW)

    elapsed_time = time.time() - start_time

    print("\n" + "=" * 60)
    print(f"HASIL SCANNING SELESAI Dalam {elapsed_time:.2f} detik")
    print(f"Jumlah Titik Potensial (>= {TARGET_MW} MW): {len(candidates)}")
    print("=" * 60)

    print(f"{'RANK':<6} | {'LATITUDE':<10} | {'LONGITUDE':<10} | {'CA (km²)':<10} | {'HEAD (m)':<10} | {'POWER (MW)':<10}")
    print("-" * 75)
    
    for c in candidates[:10]:
        print(f"{c.id:<6} | {c.lat:<10.5f} | {c.lon:<10.5f} | {c.catchment_area:<10.2f} | {c.head:<10.1f} | {c.power:<10.2f}")

if __name__ == "__main__":
    main()