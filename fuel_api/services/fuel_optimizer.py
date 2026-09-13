from typing import Any, Dict, List

MAX_VEHICLE_RANGE_MILES = 500.0
VEHICLE_MPG = 10.0
TANK_CAPACITY_GALLONS = MAX_VEHICLE_RANGE_MILES / VEHICLE_MPG  # 50.0 gallons


def plan_optimal_fuel_stops(
    route_distance_miles: float,
    candidate_stations: List[Dict[str, Any]],
    start_full_tank: bool = True
) -> Dict[str, Any]:
    """
    Computes the optimal (cost-effective) fuel stop schedule along a route.

    Vehicle Constraints:
        - Max range: 500.0 miles
        - Fuel efficiency: 10.0 MPG
        - Tank capacity: 50.0 gallons
        - Starts with full tank (500 miles range) by default.

    Optimization Strategy:
        - For routes <= 500 miles, no fuel stops are required to complete the journey.
        - For routes > 500 miles:
            1. While destination is beyond current vehicle range:
            2. Identify all stations along the corridor within the vehicle's reachable fuel window.
            3. Prioritize stations in the optimal cruising bracket (250 - 480 miles from last stop)
               to maximize segment length while maintaining safety margins.
            4. Choose the station with the lowest retail price per gallon.
            5. Calculate fuel purchased at each stop to cover travel segments at optimal rates.
            6. The final stop covers both the preceding leg and the remaining miles to destination.

    Returns:
        dict containing:
            - fuel_stops (list of dicts)
            - total_fuel_consumed_gallons (float)
            - total_fuel_cost_usd (float)
            - average_price_per_gallon (float)
            - stops_count (int)
    """
    total_gallons_consumed = round(route_distance_miles / VEHICLE_MPG, 2)

    # If route is within initial tank range, 0 fuel stops are required
    if route_distance_miles <= MAX_VEHICLE_RANGE_MILES:
        return {
            "fuel_stops": [],
            "total_fuel_consumed_gallons": total_gallons_consumed,
            "total_fuel_cost_usd": 0.0,
            "average_price_per_gallon": 0.0,
            "stops_count": 0,
            "note": "Trip distance is within maximum vehicle range (500 miles); no refueling required en route."
        }

    stations_sorted = sorted(candidate_stations, key=lambda s: s["route_mile_marker"])
    planned_stops = []
    curr_mile = 0.0
    curr_fuel_range = MAX_VEHICLE_RANGE_MILES

    while curr_mile + curr_fuel_range < route_distance_miles:
        # Reachable candidate stations within current fuel range
        reachable = [
            s for s in stations_sorted
            if curr_mile < s["route_mile_marker"] <= curr_mile + curr_fuel_range
        ]

        if not reachable:
            # Fallback if station spacing is unusually wide: look for next available station ahead
            ahead = [s for s in stations_sorted if s["route_mile_marker"] > curr_mile]
            if ahead:
                reachable = [ahead[0]]
            else:
                break

        # Refueling window preference: aim for 250 to 480 miles from current position
        ideal_window = [
            s for s in reachable
            if s["route_mile_marker"] >= curr_mile + 250.0
        ]
        if not ideal_window:
            ideal_window = [
                s for s in reachable
                if s["route_mile_marker"] >= curr_mile + 150.0
            ]
        if not ideal_window:
            ideal_window = reachable

        # Pick the cheapest station in the reachable window
        best_station = min(ideal_window, key=lambda s: s["price"])
        planned_stops.append(best_station)

        curr_mile = best_station["route_mile_marker"]
        curr_fuel_range = MAX_VEHICLE_RANGE_MILES

    # Calculate gallons and cost for each planned stop
    # Segment 1: from start (mile 0) to stop 1
    # Segment i: from stop i-1 to stop i
    # Final segment: from last stop to destination
    detailed_stops = []
    total_cost = 0.0
    last_stop_mile = 0.0

    for i, s in enumerate(planned_stops):
        leg_miles = s["route_mile_marker"] - last_stop_mile
        gallons_for_leg = leg_miles / VEHICLE_MPG

        # For the final stop, include the remaining miles to reach the destination
        is_final_stop = (i == len(planned_stops) - 1)
        if is_final_stop:
            final_leg_miles = route_distance_miles - s["route_mile_marker"]
            total_gallons_at_stop = (leg_miles + final_leg_miles) / VEHICLE_MPG
        else:
            total_gallons_at_stop = gallons_for_leg

        price_per_gal = s["price"]
        stop_cost = round(total_gallons_at_stop * price_per_gal, 2)
        total_cost += stop_cost

        detailed_stops.append({
            "stop_number": i + 1,
            "station_id": s["id"],
            "opis_id": s["opis_id"],
            "name": s["name"],
            "address": s["address"],
            "city": s["city"],
            "state": s["state"],
            "price_per_gallon": price_per_gal,
            "latitude": s["latitude"],
            "longitude": s["longitude"],
            "route_mile_marker": s["route_mile_marker"],
            "distance_from_last_stop_miles": round(leg_miles, 2),
            "gallons_pumped": round(total_gallons_at_stop, 2),
            "cost_usd": stop_cost,
        })

        last_stop_mile = s["route_mile_marker"]

    avg_price = (
        round(total_cost / total_gallons_consumed, 3)
        if total_gallons_consumed > 0 else 0.0
    )

    return {
        "fuel_stops": detailed_stops,
        "total_fuel_consumed_gallons": total_gallons_consumed,
        "total_fuel_cost_usd": round(total_cost, 2),
        "average_price_per_gallon": avg_price,
        "stops_count": len(detailed_stops),
        "note": f"Optimal plan generated with {len(detailed_stops)} fuel stops based on vehicle max range 500 miles and 10 MPG."
    }
