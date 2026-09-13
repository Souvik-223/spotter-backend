import json
import time

from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from fuel_api.serializers import RouteRequestSerializer
from fuel_api.services.fuel_optimizer import (
    MAX_VEHICLE_RANGE_MILES,
    VEHICLE_MPG,
    plan_optimal_fuel_stops,
)
from fuel_api.services.geocoding import geocode_location
from fuel_api.services.osrm_client import get_osrm_route
from fuel_api.services.spatial_index import FuelStationSpatialIndex


def build_route_plan(start_input: str, finish_input: str) -> dict:
    """
    Coordinates geocoding, single OSRM routing call, spatial corridor query,
    and fuel stop optimization. Returns full structured data and GeoJSON.
    """
    start_time = time.perf_counter()

    # 1. Geocode start and finish locations (validating within USA)
    start_lat, start_lon, start_display = geocode_location(start_input)
    finish_lat, finish_lon, finish_display = geocode_location(finish_input)

    # 2. Query free routing engine (OSRM) - Exactly 1 call
    route_data = get_osrm_route(start_lat, start_lon, finish_lat, finish_lon)
    distance_miles = route_data["distance_miles"]
    duration_minutes = route_data["duration_minutes"]
    route_coords = route_data["coordinates"]  # [[lon, lat], ...]

    # 3. Fast spatial corridor station search using in-memory cKDTree
    spatial_index = FuelStationSpatialIndex.get_instance()
    candidate_stations = spatial_index.find_stations_along_route(
        route_coords,
        corridor_radius_miles=5.0
    )

    # 4. Optimal fuel stop calculation
    optimization_result = plan_optimal_fuel_stops(
        route_distance_miles=distance_miles,
        candidate_stations=candidate_stations,
        start_full_tank=True
    )

    fuel_stops = optimization_result["fuel_stops"]

    # 5. Construct standard GeoJSON FeatureCollection
    features = [
        # Route polyline feature
        {
            "type": "Feature",
            "properties": {
                "role": "route_polyline",
                "distance_miles": distance_miles,
                "duration_minutes": duration_minutes,
                "color": "#2563eb",
                "weight": 5
            },
            "geometry": route_data["geojson_geometry"]
        },
        # Start location marker
        {
            "type": "Feature",
            "properties": {
                "role": "start_point",
                "name": start_display,
                "marker_color": "#16a34a",
                "popup": f"<strong>Start:</strong> {start_display}"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [start_lon, start_lat]
            }
        },
        # Finish location marker
        {
            "type": "Feature",
            "properties": {
                "role": "finish_point",
                "name": finish_display,
                "marker_color": "#dc2626",
                "popup": f"<strong>Destination:</strong> {finish_display}"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [finish_lon, finish_lat]
            }
        }
    ]

    # Fuel stop markers
    for stop in fuel_stops:
        features.append({
            "type": "Feature",
            "properties": {
                "role": "fuel_stop",
                "stop_number": stop["stop_number"],
                "station_name": stop["name"],
                "address": f"{stop['address']}, {stop['city']}, {stop['state']}",
                "price_per_gallon": stop["price_per_gallon"],
                "gallons_pumped": stop["gallons_pumped"],
                "cost_usd": stop["cost_usd"],
                "route_mile_marker": stop["route_mile_marker"],
                "marker_color": "#f59e0b",
                "popup": (
                    f"<strong>Stop #{stop['stop_number']}: {stop['name']}</strong><br>"
                    f"Address: {stop['address']}, {stop['city']}, {stop['state']}<br>"
                    f"Price: ${stop['price_per_gallon']:.3f}/gal<br>"
                    f"Gallons: {stop['gallons_pumped']} gal (${stop['cost_usd']:.2f})<br>"
                    f"Mile Marker: {stop['route_mile_marker']} mi"
                )
            },
            "geometry": {
                "type": "Point",
                "coordinates": [stop["longitude"], stop["latitude"]]
            }
        })

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "start_location": start_display,
        "finish_location": finish_display,
        "summary": {
            "total_distance_miles": distance_miles,
            "duration_minutes": duration_minutes,
            "total_gallons_consumed": optimization_result["total_fuel_consumed_gallons"],
            "total_fuel_cost_usd": optimization_result["total_fuel_cost_usd"],
            "average_price_per_gallon": optimization_result["average_price_per_gallon"],
            "mpg": VEHICLE_MPG,
            "max_range_miles": MAX_VEHICLE_RANGE_MILES,
            "stops_count": optimization_result["stops_count"],
            "note": optimization_result.get("note", "")
        },
        "fuel_stops": fuel_stops,
        "route_geometry": route_data["geojson_geometry"],
        "geojson": geojson_data,
        "execution_time_ms": elapsed_ms
    }


class RouteFuelPlanAPIView(APIView):
    """
    REST API endpoint to compute optimal fuel stops along a driving route in the USA.
    Accepts GET query parameters or POST JSON body with 'start' and 'finish'.
    """

    def get(self, request):
        serializer = RouteRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        start = serializer.validated_data["start"]
        finish = serializer.validated_data["finish"]

        try:
            plan = build_route_plan(start, finish)
            return Response(plan, status=status.HTTP_200_OK)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Internal routing calculation error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        serializer = RouteRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        start = serializer.validated_data["start"]
        finish = serializer.validated_data["finish"]

        try:
            plan = build_route_plan(start, finish)
            return Response(plan, status=status.HTTP_200_OK)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Internal routing calculation error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InteractiveMapView(APIView):
    """
    Renders an interactive Leaflet.js HTML map view for the route and optimal fuel stops.
    """

    def get(self, request):
        start = request.GET.get("start", "Austin, TX")
        finish = request.GET.get("finish", "Seattle, WA")

        error_message = None
        plan = None
        plan_json = "{}"

        try:
            plan = build_route_plan(start, finish)
            plan_json = json.dumps(plan)
        except Exception as e:
            error_message = str(e)

        context = {
            "start": start,
            "finish": finish,
            "plan": plan,
            "plan_json": plan_json,
            "error_message": error_message
        }
        return render(request, "map.html", context)
