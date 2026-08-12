import rasterio
import numpy as np

class HydrologyAnalyzer:
    def __init__(self, flow_acc_path):
        self.flow_acc_path = flow_acc_path
        self.src = rasterio.open(flow_acc_path)
        self.band = self.src.read(1)

    def get_catchment_area(self, lon, lat):
        try:
            row, col = self.src.index(lon, lat)
            if 0 <= row < self.src.height and 0 <= col < self.src.width:
                cell_count = self.band[row, col]
                if cell_count is not None and cell_count > 0:
                    ca_km2 = float(cell_count) * 0.000064 
                    return ca_km2
        except Exception:
            pass
        return 0.0

    def close(self):
        if self.src:
            self.src.close()