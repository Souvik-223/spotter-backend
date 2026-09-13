import csv
import os
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand

from fuel_api.models import FuelStation

# Set of valid US states + DC
US_STATES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
}

# Manual coordinate fallbacks for cities not present in the base US cities table
MANUAL_CITY_COORDINATES = {
    ('EVERGREEN', 'AL'): (31.4338, -86.9541),
    ('HENRICO', 'VA'): (37.5385, -77.3489),
    ('UNIVERSITY PARK', 'IL'): (41.4428, -87.6853),
    ('ELIZABETHPORT', 'NJ'): (40.6559, -74.1957),
    ('PORT WENTWORTH', 'GA'): (32.1494, -81.1632),
    ('BROOKPARK', 'OH'): (41.4017, -81.8218),
}


class Command(BaseCommand):
    help = "Loads and geocodes fuel prices CSV dataset into the FuelStation database table"

    def add_arguments(self, parser):
        default_csv = (
            os.path.join(settings.BASE_DIR, 'data', 'fuel-prices-for-be-assessment.csv')
            if os.path.exists(os.path.join(settings.BASE_DIR, 'data', 'fuel-prices-for-be-assessment.csv'))
            else os.path.join(settings.BASE_DIR, 'tasks', 'fuel-prices-for-be-assessment.csv')
        )
        parser.add_argument(
            '--csv-path',
            type=str,
            default=default_csv,
            help='Path to fuel prices CSV file'
        )
        parser.add_argument(
            '--cities-path',
            type=str,
            default=os.path.join(settings.BASE_DIR, 'fuel_api', 'data', 'us_cities.csv'),
            help='Path to US cities coordinates CSV file'
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        cities_path = options['cities_path']

        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f"Fuel CSV file not found: {csv_path}"))
            return

        if not os.path.exists(cities_path):
            self.stderr.write(self.style.ERROR(f"US cities CSV file not found: {cities_path}"))
            return

        self.stdout.write(self.style.NOTICE("Loading US cities coordinate database..."))
        cities_map = {}
        with open(cities_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                city = row['CITY'].strip().upper()
                state = row['STATE_CODE'].strip().upper()
                key = (city, state)
                if key not in cities_map:
                    try:
                        cities_map[key] = (float(row['LATITUDE']), float(row['LONGITUDE']))
                    except (ValueError, KeyError):
                        continue

        cities_map.update(MANUAL_CITY_COORDINATES)
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(cities_map)} city coordinates."))

        self.stdout.write(self.style.NOTICE(f"Parsing fuel prices from {csv_path}..."))
        stations_to_create = []
        skipped_non_us = 0
        skipped_unresolved = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                state = row['State'].strip().upper()
                city = row['City'].strip().upper()

                # Filter out non-US entries (e.g. Canadian provinces)
                if state not in US_STATES:
                    skipped_non_us += 1
                    continue

                coord = cities_map.get((city, state))
                if not coord:
                    skipped_unresolved += 1
                    continue

                lat, lon = coord

                try:
                    price = Decimal(row['Retail Price'].strip())
                    opis_id = int(row['OPIS Truckstop ID'].strip())
                    rack_id = int(row['Rack ID'].strip())
                except (ValueError, KeyError):
                    continue

                stations_to_create.append(FuelStation(
                    opis_id=opis_id,
                    name=row['Truckstop Name'].strip(),
                    address=row['Address'].strip(),
                    city=row['City'].strip(),
                    state=state,
                    rack_id=rack_id,
                    retail_price=price,
                    latitude=lat,
                    longitude=lon,
                ))

        self.stdout.write(self.style.NOTICE("Clearing existing FuelStation records..."))
        FuelStation.objects.all().delete()

        self.stdout.write(self.style.NOTICE(f"Bulk inserting {len(stations_to_create)} fuel stations..."))
        FuelStation.objects.bulk_create(stations_to_create, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {len(stations_to_create)} US fuel stations! "
            f"(Skipped: {skipped_non_us} non-US, {skipped_unresolved} unresolved)"
        ))
