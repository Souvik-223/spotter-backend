from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    start = serializers.CharField(
        required=True,
        help_text="Starting location in the USA (city/state, address, or lat,lon e.g. 'Austin, TX' or '30.2672,-97.7431')"
    )
    finish = serializers.CharField(
        required=True,
        help_text="Destination location in the USA (city/state, address, or lat,lon e.g. 'Seattle, WA' or '47.6062,-122.3321')"
    )


class FuelStopSerializer(serializers.Serializer):
    stop_number = serializers.IntegerField()
    station_id = serializers.IntegerField()
    opis_id = serializers.IntegerField()
    name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    price_per_gallon = serializers.FloatField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    route_mile_marker = serializers.FloatField()
    distance_from_last_stop_miles = serializers.FloatField()
    gallons_pumped = serializers.FloatField()
    cost_usd = serializers.FloatField()


class RouteSummarySerializer(serializers.Serializer):
    total_distance_miles = serializers.FloatField()
    duration_minutes = serializers.FloatField()
    total_gallons_consumed = serializers.FloatField()
    total_fuel_cost_usd = serializers.FloatField()
    average_price_per_gallon = serializers.FloatField()
    mpg = serializers.FloatField()
    max_range_miles = serializers.FloatField()
    stops_count = serializers.IntegerField()


class RoutePlanResponseSerializer(serializers.Serializer):
    start_location = serializers.CharField()
    finish_location = serializers.CharField()
    summary = RouteSummarySerializer()
    fuel_stops = FuelStopSerializer(many=True)
    route_geometry = serializers.DictField()
    geojson = serializers.DictField()
    execution_time_ms = serializers.FloatField()
