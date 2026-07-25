"""Weather log (adr-37 decision 5): an immutable per-date rainfall/weather record.

Independent of the ledger and the domain — an environmental fact the metrics read,
never an economic event. Immutable once written; a correction is another record.
"""

from django.conf import settings
from django.db import models


class WeatherLog(models.Model):
    site = models.CharField(max_length=120, blank=True)
    date = models.DateField()
    rainfall_mm = models.DecimalField(max_digits=7, decimal_places=1, default=0)
    temp_min = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    temp_max = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["site", "-date"])]

    def __str__(self):
        return f"{self.site or 'default'} {self.date} {self.rainfall_mm}mm"
