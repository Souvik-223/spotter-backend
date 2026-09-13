from typing import Any, Dict

import requests

# Conversion constant: meters to statute miles
METERS_TO_MILES = 0.000621371
SECONDS_TO_MINUTES = 1.0 / 60.0


def get_osrm_route(
    start_lat: float,
    start_lon: float,
    finish_lat: float,
    finish_lon: float,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Fetches the driving route between start and finish coordinates using the free OSRM public API.
    Makes exactly ONE call to the routing API.

    Returns:
        dict with keys:
            - distance_miles (float): Total driving distance in miles
            - duration_minutes (float): Estimated travel time in minutes
            - coordinates (list of [lon, lat]): GeoJSON polyline coordinate points
            - geojson_geometry (dict): GeoJSON LineString geometry
    """
    # OSRM expects coordinates in order: {longitude},{latitude}
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{start_lon:.6f},{start_lat:.6f};{finish_lon:.6f},{finish_lat:.6f}"
        f"?overview=full&geometries=geojson&steps=false"
    )

    headers = {
        "User-Agent": "SpotterFuelRoutePlanner/1.0 (assessment@spotter.internal)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to communicate with OSRM routing engine: {e}")

    code = data.get("code")
    if code != "Ok" or not data.get("routes"):
        msg = data.get("message", "No route found between specified coordinates.")
        raise ValueError(f"Routing engine could not calculate route: {msg}")

    primary_route = data["routes"][0]
    distance_meters = primary_route.get("distance", 0.0)
    duration_seconds = primary_route.get("duration", 0.0)
    geometry = primary_route.get("geometry", {})
    coordinates = geometry.get("coordinates", [])

    if not coordinates:
        raise ValueError("Routing engine returned empty route geometry.")

    distance_miles = distance_meters * METERS_TO_MILES
    duration_minutes = duration_seconds * SECONDS_TO_MINUTES

    return {
        "distance_miles": round(distance_miles, 2),
        "duration_minutes": round(duration_minutes, 1),
        "coordinates": coordinates,  # [[lon, lat], ...]
        "geojson_geometry": geometry
    }
