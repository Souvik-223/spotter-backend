import json
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from fuel_api.models import FuelStation
from fuel_api.services.fuel_optimizer import (
    MAX_VEHICLE_RANGE_MILES,
    plan_optimal_fuel_stops,
)
from fuel_api.services.geocoding import geocode_location, is_within_us, parse_coordinates
from fuel_api.services.spatial_index import (
    FuelStationSpatialIndex,
    haversine_miles,
)


class GeocodingServiceTests(TestCase):
    """Tests for coordinate parsing and US boundary validation."""

    def test_parse_coordinates_valid(self):
        lat, lon = parse_coordinates("30.2672, -97.7431")
        self.assertAlmostEqual(lat, 30.2672)
        self.assertAlmostEqual(lon, -97.7431)

    def test_parse_coordinates_invalid_format(self):
        res = parse_coordinates("Austin, Texas")
        self.assertIsNone(res)

    def test_is_within_us(self):
        # Austin, TX is in US
        self.assertTrue(is_within_us(30.2672, -97.7431))
        # Paris, France is not in US
        self.assertFalse(is_within_us(48.8566, 2.3522))
        # Tokyo, Japan is not in US
        self.assertFalse(is_within_us(35.6762, 139.6503))

    def test_geocode_location_direct_coords(self):
        lat, lon, name = geocode_location("30.2672, -97.7431")
        self.assertAlmostEqual(lat, 30.2672)
        self.assertAlmostEqual(lon, -97.7431)

    def test_geocode_location_out_of_bounds_coords(self):
        with self.assertRaises(ValueError):
            geocode_location("48.8566, 2.3522")  # Paris


class SpatialIndexTests(TestCase):
    """Tests for spatial distance calculations and corridor indexing."""

    def setUp(self):
        # Create test fuel stations in Texas
        FuelStation.objects.create(
            opis_id=101,
            name="Austin Test Station",
            address="100 Congress Ave",
            city="Austin",
            state="TX",
            rack_id=1,
            retail_price=2.85,
            latitude=30.2672,
            longitude=-97.7431
        )
        FuelStation.objects.create(
            opis_id=102,
            name="Waco Test Station",
            address="200 I-35",
            city="Waco",
            state="TX",
            rack_id=2,
            retail_price=2.65,
            latitude=31.5493,
            longitude=-97.1467
        )
        FuelStationSpatialIndex.get_instance().reload()

    def test_haversine_distance(self):
        # Austin (30.2672, -97.7431) to Waco (31.5493, -97.1467) is roughly 95-100 miles
        d = haversine_miles(30.2672, -97.7431, 31.5493, -97.1467)
        self.assertTrue(90.0 < d < 105.0)

    def test_find_stations_along_route(self):
        spatial_index = FuelStationSpatialIndex.get_instance()
        # Route from Austin to Waco
        route_coords = [
            [-97.7431, 30.2672],
            [-97.4500, 30.9000],
            [-97.1467, 31.5493]
        ]
        stations = spatial_index.find_stations_along_route(route_coords, corridor_radius_miles=15.0)
        self.assertTrue(len(stations) >= 1)
        # Verify route mile markers increase
        markers = [s["route_mile_marker"] for s in stations]
        self.assertEqual(markers, sorted(markers))


class FuelOptimizerTests(TestCase):
    """Tests for fuel stop optimization under vehicle constraints."""

    def test_route_under_500_miles_requires_zero_stops(self):
        result = plan_optimal_fuel_stops(
            route_distance_miles=350.0,
            candidate_stations=[],
            start_full_tank=True
        )
        self.assertEqual(result["stops_count"], 0)
        self.assertEqual(result["fuel_stops"], [])
        self.assertEqual(result["total_fuel_cost_usd"], 0.0)
        self.assertEqual(result["total_fuel_consumed_gallons"], 35.0)

    def test_long_route_refuels_within_500_mile_range(self):
        # Create simulated candidate stations along a 1,200-mile route
        simulated_stations = [
            {
                "id": 1, "opis_id": 101, "name": "Stop A", "address": "Addr A",
                "city": "City A", "state": "TX", "price": 3.20,
                "latitude": 32.0, "longitude": -97.0, "route_mile_marker": 350.0
            },
            {
                "id": 2, "opis_id": 102, "name": "Stop B (Cheaper)", "address": "Addr B",
                "city": "City B", "state": "OK", "price": 2.80,
                "latitude": 34.0, "longitude": -97.0, "route_mile_marker": 400.0
            },
            {
                "id": 3, "opis_id": 103, "name": "Stop C", "address": "Addr C",
                "city": "City C", "state": "KS", "price": 2.95,
                "latitude": 37.0, "longitude": -97.0, "route_mile_marker": 800.0
            },
        ]

        result = plan_optimal_fuel_stops(
            route_distance_miles=1200.0,
            candidate_stations=simulated_stations,
            start_full_tank=True
        )

        self.assertTrue(result["stops_count"] >= 2)
        stops = result["fuel_stops"]

        # Verify no leg exceeds 500 miles
        prev_mile = 0.0
        for s in stops:
            gap = s["route_mile_marker"] - prev_mile
            self.assertLessEqual(gap, MAX_VEHICLE_RANGE_MILES)
            prev_mile = s["route_mile_marker"]

        final_leg = 1200.0 - prev_mile
        self.assertLessEqual(final_leg, MAX_VEHICLE_RANGE_MILES)

        # Total gallons consumed should equal 1200 / 10 = 120.0
        self.assertEqual(result["total_fuel_consumed_gallons"], 120.0)
        self.assertGreater(result["total_fuel_cost_usd"], 0.0)


class RouteAPITests(TestCase):
    """End-to-end API and Map View integration tests."""

    def setUp(self):
        self.client = Client()
        FuelStation.objects.create(
            opis_id=201,
            name="Dallas Fuel Hub",
            address="123 Highway 35",
            city="Dallas",
            state="TX",
            rack_id=5,
            retail_price=2.799,
            latitude=32.7767,
            longitude=-96.7970
        )
        FuelStationSpatialIndex.get_instance().reload()

    @patch("fuel_api.views.get_osrm_route")
    @patch("fuel_api.views.geocode_location")
    def test_api_route_plan_get_success(self, mock_geocode, mock_osrm):
        mock_geocode.side_effect = [
            (30.2672, -97.7431, "Austin, TX"),
            (32.7767, -96.7970, "Dallas, TX")
        ]
        mock_osrm.return_value = {
            "distance_miles": 195.5,
            "duration_minutes": 180.0,
            "coordinates": [[-97.7431, 30.2672], [-96.7970, 32.7767]],
            "geojson_geometry": {
                "type": "LineString",
                "coordinates": [[-97.7431, 30.2672], [-96.7970, 32.7767]]
            }
        }

        url = reverse("api-route-plan")
        response = self.client.get(url, {"start": "Austin, TX", "finish": "Dallas, TX"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("fuel_stops", data)
        self.assertIn("geojson", data)
        self.assertIn("execution_time_ms", data)
        self.assertEqual(data["summary"]["total_distance_miles"], 195.5)
        self.assertEqual(data["geojson"]["type"], "FeatureCollection")

    @patch("fuel_api.views.get_osrm_route")
    @patch("fuel_api.views.geocode_location")
    def test_api_route_plan_post_success(self, mock_geocode, mock_osrm):
        mock_geocode.side_effect = [
            (30.2672, -97.7431, "Austin, TX"),
            (32.7767, -96.7970, "Dallas, TX")
        ]
        mock_osrm.return_value = {
            "distance_miles": 195.5,
            "duration_minutes": 180.0,
            "coordinates": [[-97.7431, 30.2672], [-96.7970, 32.7767]],
            "geojson_geometry": {
                "type": "LineString",
                "coordinates": [[-97.7431, 30.2672], [-96.7970, 32.7767]]
            }
        }

        url = reverse("api-route-plan")
        payload = {"start": "Austin, TX", "finish": "Dallas, TX"}
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["start_location"], "Austin, TX")

    def test_api_missing_parameters(self):
        url = reverse("api-route-plan")
        response = self.client.get(url, {"start": "Austin, TX"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("finish", response.json())

    @patch("fuel_api.views.get_osrm_route")
    @patch("fuel_api.views.geocode_location")
    def test_map_view_renders_html(self, mock_geocode, mock_osrm):
        mock_geocode.side_effect = [
            (30.2672, -97.7431, "Austin, TX"),
            (32.7767, -96.7970, "Dallas, TX")
        ]
        mock_osrm.return_value = {
            "distance_miles": 195.5,
            "duration_minutes": 180.0,
            "coordinates": [[-97.7431, 30.2672], [-96.7970, 32.7767]],
            "geojson_geometry": {
                "type": "LineString",
                "coordinates": [[-97.7431, 30.2672], [-96.7970, 32.7767]]
            }
        }

        url = reverse("interactive-map")
        response = self.client.get(url, {"start": "Austin, TX", "finish": "Dallas, TX"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Optimal Fuel Route Planner")
        self.assertContains(response, "map-container")
