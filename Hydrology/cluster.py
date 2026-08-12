import numpy as np

def filter_close_candidates(candidates, min_distance_m=1000):
    """
    Menyaring kandidat yang jaraknya terlalu berdekatan (dalam meter).
    Menggunakan pendekatan sederhana berbasis derajat lintang/bujur (~111 km per derajat).
    """
    filtered = []
    min_deg = min_distance_m / 111000.0

    # Urutkan dari power terbesar ke terkecil agar yang diambil adalah titik terbaik
    sorted_candidates = sorted(candidates, key=lambda x: x.power, reverse=True)

    for cand in sorted_candidates:
        is_too_close = False
        for kept in filtered:
            # Hitung jarak Euclidean sederhana dalam derajat
            dist = np.sqrt((cand.lat - kept.lat)**2 + (cand.lon - kept.lon)**2)
            if dist < min_deg:
                is_too_close = True
                break
        if not is_too_close:
            filtered.append(cand)

    return filtered