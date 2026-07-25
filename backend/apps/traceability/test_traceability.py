"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Phase 11 (traceability): RENSPA, DT-e and caravana (adr-38).

Establishment is an editable catalog; TransitDocument and Caravana are immutable events
that post no ledger entry. The DT-e service gates inactive/equal establishments, a
non-positive head count and a duplicate number; the caravana service gates a non-active
animal and a duplicate official number. Coverage is null when there is no active head.
"""

from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.clients.models import Client
from apps.ledger.models import LedgerEntry
from apps.livestock.models import Animal, Category
from apps.metrics.services import caravana_coverage
from apps.traceability.models import Caravana, Establishment, TransitDocument
from apps.traceability.services import register_caravana, register_transit

pytestmark = pytest.mark.django_db


def _establishments():
    origin = Establishment.objects.create(renspa="01.001.0.00001/00", name="Campo A")
    dest = Establishment.objects.create(renspa="01.001.0.00002/00", name="Feedlot B")
    return origin, dest


def _animal(client, ear_tag="A1", status=Animal.Status.ACTIVE):
    return Animal.objects.create(
        client=client, ear_tag=ear_tag, category=Category.STEER,
        status=status, entry_date=date(2026, 7, 1),
    )


def test_transit_links_two_establishments():
    origin, dest = _establishments()
    dte = register_transit(
        dte_number="DTE-1", origin=origin, destination=dest,
        date=date(2026, 7, 10), head_count=20,
    )
    assert dte.origin_id == origin.id
    assert dte.destination_id == dest.id
    assert TransitDocument.objects.count() == 1


def test_transit_posts_no_ledger_entry():
    origin, dest = _establishments()
    register_transit(
        dte_number="DTE-2", origin=origin, destination=dest,
        date=date(2026, 7, 10), head_count=5,
    )
    assert LedgerEntry.objects.count() == 0


def test_transit_rejects_inactive_establishment():
    origin, dest = _establishments()
    dest.is_active = False
    dest.save(update_fields=["is_active"])
    with pytest.raises(ValidationError):
        register_transit(
            dte_number="DTE-3", origin=origin, destination=dest,
            date=date(2026, 7, 10), head_count=5,
        )
    assert TransitDocument.objects.count() == 0


def test_transit_rejects_self_transit():
    origin, _ = _establishments()
    with pytest.raises(ValidationError):
        register_transit(
            dte_number="DTE-4", origin=origin, destination=origin,
            date=date(2026, 7, 10), head_count=5,
        )


def test_transit_rejects_non_positive_head_count():
    origin, dest = _establishments()
    with pytest.raises(ValidationError):
        register_transit(
            dte_number="DTE-5", origin=origin, destination=dest,
            date=date(2026, 7, 10), head_count=0,
        )


def test_transit_rejects_duplicate_dte_number():
    origin, dest = _establishments()
    register_transit(
        dte_number="DTE-6", origin=origin, destination=dest,
        date=date(2026, 7, 10), head_count=5,
    )
    with pytest.raises(ValidationError):
        register_transit(
            dte_number="DTE-6", origin=origin, destination=dest,
            date=date(2026, 7, 11), head_count=8,
        )


def test_caravana_binds_to_active_animal():
    client = Client.objects.create(name="Don Aldo", kind=Client.Kind.BOARDING)
    animal = _animal(client)
    caravana = register_caravana(
        official_number="AR-0001", animal=animal, assigned_date=date(2026, 7, 5)
    )
    assert caravana.animal_id == animal.id
    assert LedgerEntry.objects.count() == 0


def test_caravana_rejects_non_active_animal():
    client = Client.objects.create(name="Don Aldo", kind=Client.Kind.BOARDING)
    dead = _animal(client, ear_tag="D1", status=Animal.Status.DEAD)
    with pytest.raises(ValidationError):
        register_caravana(
            official_number="AR-0002", animal=dead, assigned_date=date(2026, 7, 5)
        )
    assert Caravana.objects.count() == 0


def test_caravana_rejects_duplicate_official_number():
    client = Client.objects.create(name="Don Aldo", kind=Client.Kind.BOARDING)
    a1 = _animal(client, ear_tag="A1")
    a2 = _animal(client, ear_tag="A2")
    register_caravana(official_number="AR-0003", animal=a1, assigned_date=date(2026, 7, 5))
    with pytest.raises(ValidationError):
        register_caravana(official_number="AR-0003", animal=a2, assigned_date=date(2026, 7, 6))


def test_coverage_is_ratio_over_active_head():
    client = Client.objects.create(name="Don Aldo", kind=Client.Kind.BOARDING)
    a1 = _animal(client, ear_tag="A1")
    _animal(client, ear_tag="A2")  # active, uncaravanned
    register_caravana(official_number="AR-0004", animal=a1, assigned_date=date(2026, 7, 5))
    report = caravana_coverage(client=client)
    assert report["active_head"] == 2
    assert report["caravanned"] == 1
    assert report["ratio"] == Decimal("1") / Decimal("2")
    assert report["not_calculable"] is None


def test_coverage_is_null_without_active_head():
    client = Client.objects.create(name="Sin hacienda", kind=Client.Kind.BOARDING)
    report = caravana_coverage(client=client)
    assert report["ratio"] is None
    assert report["not_calculable"] == "no_active_head"
