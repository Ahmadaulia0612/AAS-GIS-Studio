"""
Auto RBI locator / validator.

This module is intentionally independent from NASA, CHIRPS and the
Watershed engine. It provides lightweight reverse-geocoding of an outlet
coordinate and geometry-based validation of an RBI file.
"""

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class RBILocator:
    """Locate an outlet administratively and validate an RBI vector file."""

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

    def __init__(self, user_agent="AAS-GIS-Studio/2.0"):
        self.user_agent = user_agent

    def reverse_geocode(self, latitude, longitude, timeout=10):
        """Return a small administrative dictionary for an outlet."""
        params = urlencode(
            {
                "lat": float(latitude),
                "lon": float(longitude),
                "format": "jsonv2",
                "addressdetails": 1,
                "zoom": 10,
            }
        )

        request = Request(
            f"{self.NOMINATIM_URL}?{params}",
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            },
        )

        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        address = data.get("address", {})

        # Indonesia commonly exposes municipality names through county /
        # city / state_district depending on the exact point.
        kabupaten = (
            address.get("county")
            or address.get("city_district")
            or address.get("municipality")
            or address.get("city")
        )

        province = address.get("state") or address.get("province")

        return {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "display_name": data.get("display_name", ""),
            "kabupaten": kabupaten or "",
            "province": province or "",
            "country": address.get("country", ""),
            "country_code": address.get("country_code", "").upper(),
        }

    @staticmethod
    def suggested_rbi_name(location):
        """Build the user-facing RBI recommendation."""
        kabupaten = (location.get("kabupaten") or "").strip()
        if not kabupaten:
            return "RBI sesuai lokasi outlet"

        # Avoid duplicate 'Kabupaten' when the geocoder already supplied it.
        clean = kabupaten
        if clean.lower().startswith("kabupaten "):
            clean = clean[10:].strip()

        return f"RBI {clean}"

    @staticmethod
    def validate_rbi_contains_outlet(path, latitude, longitude):
        """Check whether an RBI vector dataset contains the outlet point.

        Uses GeoPandas only when validation is requested, so this module does
        not add any work to normal Watershed/NASA/CHIRPS startup.
        """
        import geopandas as gpd
        from shapely.geometry import Point

        if not path or not os.path.exists(path):
            return {
                "valid": False,
                "contains": False,
                "message": "File RBI tidak ditemukan.",
            }

        gdf = gpd.read_file(path)

        if gdf.empty or gdf.geometry is None:
            return {
                "valid": False,
                "contains": False,
                "message": "File RBI tidak memiliki geometri.",
            }

        if gdf.crs is None:
            return {
                "valid": False,
                "contains": False,
                "message": "RBI tidak memiliki CRS metadata.",
            }

        point = gpd.GeoSeries(
            [Point(float(longitude), float(latitude))],
            crs="EPSG:4326",
        ).to_crs(gdf.crs).iloc[0]

        contains = bool(gdf.geometry.intersects(point).any())

        return {
            "valid": True,
            "contains": contains,
            "message": (
                "RBI mencakup outlet."
                if contains
                else "RBI tidak mencakup outlet."
            ),
        }
