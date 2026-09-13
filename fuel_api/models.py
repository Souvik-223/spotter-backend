from django.db import models


class FuelStation(models.Model):
    """
    Represents a fuel station / truck stop with retail pricing and spatial coordinates.
    """
    opis_id = models.IntegerField(db_index=True, help_text="OPIS Truckstop ID")
    name = models.CharField(max_length=255, help_text="Truckstop Name")
    address = models.CharField(max_length=255, help_text="Street Address")
    city = models.CharField(max_length=100, db_index=True, help_text="City Name")
    state = models.CharField(max_length=2, db_index=True, help_text="2-letter State Code")
    rack_id = models.IntegerField(help_text="Rack ID")
    retail_price = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        db_index=True,
        help_text="Retail Price per Gallon in USD"
    )
    latitude = models.FloatField(db_index=True, help_text="WGS84 Latitude")
    longitude = models.FloatField(db_index=True, help_text="WGS84 Longitude")

    class Meta:
        verbose_name = "Fuel Station"
        verbose_name_plural = "Fuel Stations"
        indexes = [
            models.Index(fields=['state', 'city']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state} (${self.retail_price:.3f}/gal)"

