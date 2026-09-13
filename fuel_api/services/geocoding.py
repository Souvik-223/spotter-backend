import re
import urllib.parse
from typing import Optional, Tuple

import requests

# In-memory geocoding cache to minimize network calls
_GEOCODE_CACHE: dict[str, Tuple[float, float, str]] = {}

# Approximate bounding box for the Continental United States (and Alaska/Hawaii)
US_LAT_MIN, US_LAT_MAX = 18.0, 72.0
US_LON_MIN, US_LON_MAX = -180.0, -65.0

# Continental US strict bounds for road trip validity
CONUS_LAT_MIN, CONUS_LAT_MAX = 24.0, 50.0
CONUS_LON_MIN, CONUS_LON_MAX = -125.0, -66.0


def is_within_us(lat: float, lon: float, strict_continental: bool = True) -> bool:
    """Check if given coordinates fall within the United States."""
    if strict_continental:
        return CONUS_LAT_MIN <= lat <= CONUS_LAT_MAX and CONUS_LON_MIN <= lon <= CONUS_LON_MAX
    return US_LAT_MIN <= lat <= US_LAT_MAX and US_LON_MIN <= lon <= US_LON_MAX


def parse_coordinates(location_str: str) -> Optional[Tuple[float, float]]:
    """
    Attempts to parse comma-separated lat, lon string.
    Example: "30.2672, -97.7431" -> (30.2672, -97.7431)
    """
    match = re.match(r"^([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)$", location_str.strip())
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        return lat, lon
    return None


def geocode_location(location_str: str, timeout: int = 6) -> Tuple[float, float, str]:
    """
    Resolves a location string (address, city/state, or lat,lon) to (lat, lon, display_name).
    Enforces that the location is within the United States.
    """
    clean_str = location_str.strip()
    if not clean_str:
        raise ValueError("Location string cannot be empty.")

    # Check if input is directly lat, lon coordinates
    coords = parse_coordinates(clean_str)
    if coords:
        lat, lon = coords
        if not is_within_us(lat, lon):
            raise ValueError(
                f"Coordinates ({lat}, {lon}) are outside the Continental United States."
            )
        return lat, lon, f"Location ({lat:.4f}, {lon:.4f})"

    cache_key = clean_str.lower()
    if cache_key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[cache_key]

    # Geocode using OpenStreetMap Nominatim
    url = (
        f"https://nominatim.openstreetmap.org/search?"
        f"q={urllib.parse.quote(clean_str)}&format=json&countrycodes=us&limit=1"
    )
    headers = {
        "User-Agent": "SpotterFuelRoutePlanner/1.0 (assessment@spotter.internal)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        results = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Geocoding service unavailable: {e}")

    if not results:
        raise ValueError(
            f"Could not resolve location '{clean_str}' within the United States. "
            f"Please check the spelling or provide 'City, State' or 'lat,lon'."
        )

    item = results[0]
    lat = float(item["lat"])
    lon = float(item["lon"])
    display_name = item.get("display_name", clean_str)

    if not is_within_us(lat, lon):
        raise ValueError(
            f"Resolved location '{display_name}' ({lat}, {lon}) is outside the Continental United States."
        )

    _GEOCODE_CACHE[cache_key] = (lat, lon, display_name)
    return lat, lon, display_name
