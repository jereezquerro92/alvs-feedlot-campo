"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Derived reproductive and genetic metrics (adr-46 decision 8, adr-47 decision 8).

Every rate is a ratio of two honest event counts; a missing denominator returns
`None` plus a reason, never a fabricated zero (adr-29 rule 2).
"""

from decimal import Decimal

import pytest

from apps.clients.models import Client
from apps.genetics.models import Direction as MoveDir, SemenBatch, Sire
from apps.genetics.services import register_semen_movement
from apps.livestock.models import Animal, Category
from apps.breeding.models import Method, PregnancyMethod, PregnancyResult, CalvingOutcome
from apps.breeding.services import (
    register_calving,
    register_pregnancy_check,
    register_service,
    register_weaning,
)
from apps.metrics import services

pytestmark = pytest.mark.django_db


def _client(name="La Cría", kind=Client.Kind.BOARDING):
    return Client.objects.create(name=name, kind=kind)


def _cow(client, ear_tag="V-001"):
    return Animal.objects.create(
        client=client, ear_tag=ear_tag, category=Category.COW, sex="female",
        entry_date="2026-01-10",
    )


def _service(cow, date="2026-02-01"):
    return register_service(animal=cow, date=date, method=Method.NATURAL)


# --- pregnancy_rate ----------------------------------------------------------

def test_pregnancy_rate_is_pregnant_over_serviced():
    client = _client()
    cow = _cow(client)
    _service(cow)
    register_pregnancy_check(
        animal=cow, date="2026-03-01", method=PregnancyMethod.PALPATION,
        result=PregnancyResult.PREGNANT,
    )
    out = services.pregnancy_rate(client=client)
    assert out["serviced"] == 1
    assert out["pregnant"] == 1
    assert out["rate"] == Decimal("1")
    assert out["not_calculable"] == ""


def test_pregnancy_rate_none_without_services():
    client = _client()
    out = services.pregnancy_rate(client=client)
    assert out["rate"] is None
    assert out["not_calculable"] == "no_services_in_period"


# --- calving_rate ------------------------------------------------------------

def test_calving_rate_is_calvings_over_pregnant():
    client = _client()
    cow = _cow(client)
    register_pregnancy_check(
        animal=cow, date="2026-03-01", method=PregnancyMethod.PALPATION,
        result=PregnancyResult.PREGNANT,
    )
    register_calving(animal=cow, date="2026-11-01", outcome=CalvingOutcome.LIVE)
    out = services.calving_rate(client=client)
    assert out["pregnant"] == 1
    assert out["calvings"] == 1
    assert out["rate"] == Decimal("1")


def test_calving_rate_none_without_pregnancy_checks():
    client = _client()
    out = services.calving_rate(client=client)
    assert out["rate"] is None
    assert out["not_calculable"] == "no_pregnancy_checks"


# --- weaning_rate ------------------------------------------------------------

def test_weaning_rate_is_weanings_over_calvings():
    client = _client()
    cow = _cow(client)
    register_calving(animal=cow, date="2026-11-01", outcome=CalvingOutcome.LIVE)
    register_weaning(animal=cow, date="2027-05-01", weaning_weight="180")
    out = services.weaning_rate(client=client)
    assert out["calvings"] == 1
    assert out["weanings"] == 1
    assert out["rate"] == Decimal("1")


def test_weaning_rate_none_without_calvings():
    client = _client()
    out = services.weaning_rate(client=client)
    assert out["rate"] is None
    assert out["not_calculable"] == "no_calvings"


# --- calving_interval (IEP) --------------------------------------------------

def test_calving_interval_averages_days_between_successive_calvings():
    client = _client()
    cow = _cow(client)
    register_calving(animal=cow, date="2026-01-01", outcome=CalvingOutcome.LIVE)
    register_calving(animal=cow, date="2027-01-01", outcome=CalvingOutcome.LIVE)
    out = services.calving_interval(client=client)
    assert out["average_days"] == Decimal("365")
    assert out["not_calculable"] == ""


def test_calving_interval_none_with_a_single_calving():
    client = _client()
    cow = _cow(client)
    register_calving(animal=cow, date="2026-01-01", outcome=CalvingOutcome.LIVE)
    out = services.calving_interval(client=client)
    assert out["average_days"] is None
    assert out["not_calculable"] == "insufficient_calving_history"


# --- kg_weaned_per_dam -------------------------------------------------------

def test_kg_weaned_per_dam_divides_total_by_dams():
    client = _client()
    cow_a = _cow(client, "V-001")
    cow_b = _cow(client, "V-002")
    register_weaning(animal=cow_a, date="2027-05-01", weaning_weight="180")
    register_weaning(animal=cow_b, date="2027-05-01", weaning_weight="200")
    out = services.kg_weaned_per_dam(client=client)
    assert out["dams"] == 2
    assert out["total_kg"] == Decimal("380")
    assert out["kg_per_dam"] == Decimal("190")


def test_kg_weaned_per_dam_none_without_weanings():
    client = _client()
    out = services.kg_weaned_per_dam(client=client)
    assert out["kg_per_dam"] is None
    assert out["not_calculable"] == "no_weanings"


# --- reproduction aggregator -------------------------------------------------

def test_reproduction_returns_all_five_metrics():
    client = _client()
    out = services.reproduction(client=client)
    assert set(out) == {
        "pregnancy_rate", "calving_rate", "weaning_rate",
        "calving_interval", "kg_weaned_per_dam",
    }


# --- semen_stock_report (adr-47) ---------------------------------------------

def _stocked_batch(sire, straws="20"):
    batch = SemenBatch.objects.create(sire=sire, batch_code="B-001")
    register_semen_movement(
        semen_batch=batch, direction=MoveDir.IN, straws=straws,
        reason="purchase", date="2026-02-01",
    )
    return batch


def test_semen_stock_report_derives_straws_and_usage():
    sire = Sire.objects.create(name="Toro A", breed="Angus")
    batch = _stocked_batch(sire, "20")
    register_semen_movement(
        semen_batch=batch, direction=MoveDir.OUT, straws="2",
        reason="insemination", date="2026-03-01",
    )
    out = services.semen_stock_report()
    assert out["total_available"] == Decimal("18")
    assert out["not_calculable"] == ""
    by_sire = {row["sire"]: row for row in out["per_sire"]}
    assert by_sire[sire.id]["straws"] == Decimal("18")
    assert by_sire[sire.id]["used"] == Decimal("2")


def test_semen_stock_report_none_without_movements():
    out = services.semen_stock_report()
    assert out["total_available"] is None
    assert out["not_calculable"] == "no_semen_movements"
