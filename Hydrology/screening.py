from dataclasses import dataclass

@dataclass
class Candidate:
    id: int
    lat: float
    lon: float
    catchment_area: float
    head: float
    discharge: float
    power: float

class ScreeningEngine:
    def __init__(self):
        self.candidates = []

    def add(self, lat, lon, catchment_area, head, discharge, power):
        candidate = Candidate(
            id=len(self.candidates) + 1,
            lat=lat,
            lon=lon,
            catchment_area=catchment_area,
            head=head,
            discharge=discharge,
            power=power
        )
        self.candidates.append(candidate)

    def filter(self, minimum_power):
        result = []
        for c in self.candidates:
            if c.power >= minimum_power:
                result.append(c)
        return result

    def ranking(self):
        # Urutkan berdasarkan power terbesar ke terkecil
        self.candidates.sort(
            key=lambda x: x.power,
            reverse=True
        )
        
        # Perbarui ulang ID/Rank berdasarkan urutan baru yang sudah di-sorting
        for idx, candidate in enumerate(self.candidates):
            candidate.id = idx + 1
            
        return self.candidates

    def clear(self):
        self.candidates.clear()