import math
from typing import Any, Dict, List, Optional

import numpy as np
from scipy.spatial import cKDTree

# Mean radius of the Earth in statute miles
EARTH_RADIUS_MILES = 3958.7613


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in statute miles."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_MILES * c


def latlon_to_cartesian_3d(lat_deg: float, lon_deg: float) -> np.ndarray:
    """Convert spherical latitude/longitude to 3D Cartesian coordinates on Earth sphere."""
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)
    x = EARTH_RADIUS_MILES * math.cos(lat_rad) * math.cos(lon_rad)
    y = EARTH_RADIUS_MILES * math.cos(lat_rad) * math.sin(lon_rad)
    z = EARTH_RADIUS_MILES * math.sin(lat_rad)
    return np.array([x, y, z])


class FuelStationSpatialIndex:
    """
    In-memory spatial index utilizing scipy's cKDTree for sub-millisecond
    candidate fuel station retrieval along highway corridors.
    """
    _instance: Optional['FuelStationSpatialIndex'] = None

    def __init__(self):
        self.stations_data: List[Dict[str, Any]] = []
        self.tree: Optional[cKDTree] = None
        self._build_index()

    @classmethod
    def get_instance(cls) -> 'FuelStationSpatialIndex':
        """Singleton accessor ensuring the KDTree is built only once in memory."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _build_index(self):
        """Loads all FuelStation records from SQLite and constructs the 3D KDTree."""
        from fuel_api.models import FuelStation

        stations = list(FuelStation.objects.all())
        if not stations:
            return

        self.stations_data = []
        cartesian_points = []

        for s in stations:
            self.stations_data.append({
                "id": s.id,
                "opis_id": s.opis_id,
                "name": s.name,
                "address": s.address,
                "city": s.city,
                "state": s.state,
                "rack_id": s.rack_id,
                "price": float(s.retail_price),
                "latitude": s.latitude,
                "longitude": s.longitude,
            })
            pt_3d = latlon_to_cartesian_3d(s.latitude, s.longitude)
            cartesian_points.append(pt_3d)

        self.tree = cKDTree(np.array(cartesian_points))

    def reload(self):
        """Force rebuild of spatial index, e.g. after database seeding."""
        self._build_index()

    def find_stations_along_route(
        self,
        route_coords: List[List[float]],
        corridor_radius_miles: float = 5.0,
        subsample_step_miles: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        Finds all fuel stations within corridor_radius_miles of the route polyline.
        Each station is mapped with its projected route_mile_marker (cumulative miles from start).

        Args:
            route_coords: List of [longitude, latitude] coordinates from OSRM.
            corridor_radius_miles: Maximum perpendicular distance to consider a station along route.
            subsample_step_miles: Interval distance between KDTree search probe points.

        Returns:
            List of station dicts sorted by cumulative route_mile_marker.
        """
        if self.tree is None or not self.stations_data or len(route_coords) < 2:
            return []

        # 1. Compute cumulative distance at each vertex along the route polyline
        cum_dist = [0.0]
        for i in range(1, len(route_coords)):
            prev_lon, prev_lat = route_coords[i - 1]
            curr_lon, curr_lat = route_coords[i]
            d = haversine_miles(prev_lat, prev_lon, curr_lat, curr_lon)
            cum_dist.append(cum_dist[-1] + d)

        # 2. Sample probe points along the polyline approximately every subsample_step_miles
        probe_indices = [0]
        last_probed_mile = 0.0

        for i, m in enumerate(cum_dist):
            if m - last_probed_mile >= subsample_step_miles:
                probe_indices.append(i)
                last_probed_mile = m
        if probe_indices[-1] != len(route_coords) - 1:
            probe_indices.append(len(route_coords) - 1)

        # 3. Query KDTree for candidate station indices at each probe point
        candidate_indices = set()
        # Search radius in 3D chord distance: chord ≈ radius for small angles
        search_radius = corridor_radius_miles + subsample_step_miles

        for idx in probe_indices:
            lon, lat = route_coords[idx]
            pt_3d = latlon_to_cartesian_3d(lat, lon)
            found = self.tree.query_ball_point(pt_3d, r=search_radius)
            candidate_indices.update(found)

        if not candidate_indices:
            return []

        # 4. For each candidate station, find its closest route point and cumulative mile marker
        results = []
        for s_idx in candidate_indices:
            station = self.stations_data[s_idx]
            s_lat = station["latitude"]
            s_lon = station["longitude"]

            # Fast search: find closest vertex along route
            min_dist_to_vertex = float('inf')
            best_vertex_idx = 0

            # Only check vertices near the station
            for v_idx in probe_indices:
                v_lon, v_lat = route_coords[v_idx]
                d = haversine_miles(s_lat, s_lon, v_lat, v_lon)
                if d < min_dist_to_vertex:
                    min_dist_to_vertex = d
                    best_vertex_idx = v_idx

            # Refine within local window of vertices around best_vertex_idx
            window_start = max(0, best_vertex_idx - 15)
            window_end = min(len(route_coords), best_vertex_idx + 16)

            closest_mile = cum_dist[best_vertex_idx]
            closest_dist = min_dist_to_vertex

            for v_i in range(window_start, window_end):
                v_lon, v_lat = route_coords[v_i]
                d = haversine_miles(s_lat, s_lon, v_lat, v_lon)
                if d < closest_dist:
                    closest_dist = d
                    closest_mile = cum_dist[v_i]

            # Filter out stations beyond the corridor threshold
            if closest_dist <= corridor_radius_miles:
                results.append({
                    "id": station["id"],
                    "opis_id": station["opis_id"],
                    "name": station["name"],
                    "address": station["address"],
                    "city": station["city"],
                    "state": station["state"],
                    "price": station["price"],
                    "latitude": station["latitude"],
                    "longitude": station["longitude"],
                    "route_mile_marker": round(closest_mile, 2),
                    "corridor_offset_miles": round(closest_dist, 2),
                })

        # 5. Deduplicate and filter: If stations are at the exact same location/mile marker,
        # keep the one with the lowest retail price
        results.sort(key=lambda x: (x["route_mile_marker"], x["price"]))

        deduped: List[Dict[str, Any]] = []
        for item in results:
            if deduped:
                prev = deduped[-1]
                # If within 0.5 miles and same name or higher price, skip or replace
                if abs(item["route_mile_marker"] - prev["route_mile_marker"]) < 0.5:
                    if item["price"] < prev["price"]:
                        deduped[-1] = item
                    continue
            deduped.append(item)

        return deduped
