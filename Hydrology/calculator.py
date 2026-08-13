import os
import json

class HydropowerCalculator:
    @staticmethod
    def calculate(catchment_area_km2, gross_head_m, cf_percent=60.0):
        """
        Menghitung parameter PLTA/PLTM sesuai standar formula lembar kerja:
        - Design Flow (Q) = Berdasarkan estimasi spesifik / persentase CA atau koefisien aliran
        - Installed Capacity (MW) = 0.008 * Q * H
        - Annual Energy (GWh) = Capacity * CF * 8.76
        """
        try:
            ca = float(catchment_area_km2)
            h = float(gross_head_m)
            cf = float(cf_percent) / 100.0  # Konversi persen ke desimal (misal 60% -> 0.6)

            # Estimasi Design Flow (Q) standar empiris berbasis Catchment Area (bisa disesuaikan atau dari debit andalan)
            # Menggunakan asumsi koefisien debit spesifik ~ 0.03 m3/s per km2 (atau sesuai data empiris wilayah)
            q_design = ca * 0.032 

            # Formula Installed Capacity (MW) sesuai standar Excel verifikasi: P = 0.008 * Q * H
            installed_capacity_mw = 0.008 * q_design * h

            # Formula Annual Energy (GWh/tahun) = Capacity * CF * 8.76
            annual_energy_gwh = installed_capacity_mw * cf * 8.76

            return {
                "catchment_area_km2": round(ca, 3),
                "gross_head_m": round(h, 2),
                "design_flow_m3s": round(q_design, 3),
                "installed_capacity_mw": round(installed_capacity_mw, 3),
                "capacity_factor_percent": float(cf_percent),
                "annual_energy_gwh": round(annual_energy_gwh, 3)
            }
        except Exception as e:
            raise Exception(f"Gagal menghitung potensi energi: {str(e)}")