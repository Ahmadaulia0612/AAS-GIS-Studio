import rasterio
import numpy as np

class TerrainAnalyzer:
    def __init__(self, dem_path):
        self.dem_path = dem_path
        self.src = rasterio.open(dem_path)
        self.band = self.src.read(1)

    def get_elevation(self, lon, lat):
        try:
            row, col = self.src.index(lon, lat)
            if 0 <= row < self.src.height and 0 <= col < self.src.width:
                elev = self.band[row, col]
                if elev is not None and not np.isnan(elev) and elev > -9999:
                    return float(elev)
        except Exception:
            pass
        return None

    def close(self):
        if self.src:
            self.src.close()