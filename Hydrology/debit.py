from Hydrology.config import RUNOFF_COEFFICIENT

class DischargeCalculator:
    def calculate(self, catchment_area):
        discharge = catchment_area * RUNOFF_COEFFICIENT
        return discharge