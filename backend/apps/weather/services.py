"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Weather services — the only sanctioned write path for a weather log (adr-37).

Validates non-negative rainfall and a coherent temperature range; posts no ledger
entry and touches no domain data.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.weather.models import WeatherLog

ZERO = Decimal("0")


@transaction.atomic
def register_weather_log(
    *, date, rainfall_mm=ZERO, site="", temp_min=None, temp_max=None, note="",
    created_by=None,
):
    """Record a weather log, idempotent by (site, date).

    Re-registration updates the existing row (adr-37 rule 5 amendment) so a
    correction replaces values instead of adding another Sum() entry.
    """
    if rainfall_mm is not None and Decimal(rainfall_mm) < ZERO:
        raise ValidationError("Rainfall cannot be negative.")
    if temp_min is not None and temp_max is not None and Decimal(temp_max) < Decimal(temp_min):
        raise ValidationError("temp_max cannot be below temp_min.")

    log, _created = WeatherLog.objects.update_or_create(
        site=site or "",
        date=date,
        defaults={
            "rainfall_mm": rainfall_mm if rainfall_mm is not None else ZERO,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "note": note,
            "created_by": created_by,
        },
    )
    return log
