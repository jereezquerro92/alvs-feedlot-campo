"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Phase 10 (weather): the immutable per-date weather log (adr-37 decision 5).

Independent of the ledger and the domain. Non-negative rainfall and a coherent
temperature range are enforced in the service; the metric summarises a period.
"""

from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.metrics.services import rainfall_summary
from apps.weather.models import WeatherLog
from apps.weather.services import register_weather_log

pytestmark = pytest.mark.django_db


def test_register_weather_log_persists_a_record():
    log = register_weather_log(date=date(2026, 7, 1), rainfall_mm=Decimal("12.5"), site="Pivote 1")
    assert WeatherLog.objects.count() == 1
    assert log.rainfall_mm == Decimal("12.5")
    assert log.site == "Pivote 1"


def test_negative_rainfall_is_rejected():
    with pytest.raises(ValidationError):
        register_weather_log(date=date(2026, 7, 1), rainfall_mm=Decimal("-3"))
    assert WeatherLog.objects.count() == 0


def test_temp_max_below_min_is_rejected():
    with pytest.raises(ValidationError):
        register_weather_log(
            date=date(2026, 7, 1), temp_min=Decimal("15"), temp_max=Decimal("8")
        )


def test_rainfall_summary_totals_period_and_counts_rainy_days():
    register_weather_log(date=date(2026, 7, 1), rainfall_mm=Decimal("10"))
    register_weather_log(date=date(2026, 7, 2), rainfall_mm=Decimal("0"))
    register_weather_log(date=date(2026, 7, 3), rainfall_mm=Decimal("5.5"))
    # Outside the window — must be excluded.
    register_weather_log(date=date(2026, 8, 1), rainfall_mm=Decimal("99"))

    summary = rainfall_summary(start=date(2026, 7, 1), end=date(2026, 7, 31))
    assert summary["total_mm"] == Decimal("15.5")
    assert summary["rainy_days"] == 2
    assert summary["days_logged"] == 3


def test_rainfall_summary_is_scoped_by_site():
    register_weather_log(date=date(2026, 7, 1), rainfall_mm=Decimal("10"), site="A")
    register_weather_log(date=date(2026, 7, 1), rainfall_mm=Decimal("4"), site="B")
    summary = rainfall_summary(start=date(2026, 7, 1), end=date(2026, 7, 31), site="A")
    assert summary["total_mm"] == Decimal("10")
