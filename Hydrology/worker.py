import time
from PySide6.QtCore import QThread, Signal
from Hydrology.engine import HydrologyEngine

class HydrologyWorker(QThread):
    progress_signal = Signal(int, str)
    finished_signal = Signal(str, float, float)  # (pesan, durasi, luas_area)
    error_signal = Signal(str)

    def __init__(self, dem_files, river_file, outlet):
        super().__init__()
        self.dem_files = dem_files
        self.river_file = river_file
        self.outlet = outlet

    def run(self):
        start_time = time.time()
        try:
            self.progress_signal.emit(10, "Menginisialisasi Engine Hidrologi...")
            engine = HydrologyEngine(
                dem_files=self.dem_files, 
                river_file=self.river_file, 
                outlet=self.outlet
            )

            self.progress_signal.emit(40, "Memproses Terrain & Watershed...")
            engine.run()
            
            # Ambil nilai luas area dari engine
            area_km2 = getattr(engine, 'last_area_km2', 0.0)

            self.progress_signal.emit(100, "Selesai!")

            end_time = time.time()
            duration = end_time - start_time

            self.finished_signal.emit("Catchment Area berhasil dikerjakan!", duration, area_km2)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_signal.emit(str(e))