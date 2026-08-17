from pathlib import Path
import shutil
from datetime import datetime

target = Path("Hydrology/engine.py")

if not target.exists():
    raise SystemExit(f"Tidak ditemukan: {target}")

text = target.read_text(encoding="utf-8-sig")

old = """            # Tidak ada DEM tambahan
            if len(expanded) == len(selected):

                raise RuntimeError(
                    "Watershed menyentuh batas "
                    "DEM tetapi tidak ada DEM "
                    "tambahan yang tersedia."
                )

            selected = expanded
"""

new = """            # Jika tidak ada DEM tambahan, jangan gagal hanya
            # karena polygon watershed menyentuh tepi raster.
            #
            # Outlet sudah dipastikan berada di dalam DEM pada
            # delineate_watershed(). Jadi hasil CA tetap dipakai
            # berdasarkan DEM yang tersedia.
            if len(expanded) == len(selected):

                print()
                print("=" * 60)
                print(
                    "WARNING: Watershed menyentuh edge DEM."
                )
                print(
                    "Tidak ada DEM tambahan yang tersedia."
                )
                print(
                    "Outlet berada di dalam DEM; "
                    "hasil CA tetap digunakan."
                )
                print(
                    f"CA = {area_km2:.3f} km²"
                )
                print("=" * 60)

                return area_km2

            selected = expanded
"""

if old not in text:
    raise SystemExit(
        "Blok validasi edge DEM tidak ditemukan. File tidak diubah."
    )

backup = target.with_name(
    f"engine.py.bak_before_edge_fix_{datetime.now():%Y%m%d_%H%M%S}"
)
shutil.copy2(target, backup)

target.write_text(
    text.replace(old, new, 1),
    encoding="utf-8"
)

print("BERHASIL")
print(f"Engine: {target}")
print(f"Backup : {backup}")
