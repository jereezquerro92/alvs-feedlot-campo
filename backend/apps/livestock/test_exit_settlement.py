"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Phase 4c: sale settlement (adr-43).

A `kind=sale` exit settles through the ledger, differentiated by `Client.kind`:
boarding cattle charge an engorde commission (a `service` debit); own cattle
record the produced value as a `sale` credit. Every missing input takes the
honest cut and posts nothing (adr-29 rule 2) — a fabricated ledger entry moves a
real balance and is worse than a fabricated metric.
"""

from decimal import Decimal

import pytest

from apps.clients.models import Client
from apps.ledger.models import Concept, Direction, LedgerEntry
from apps.livestock.models import Animal, Exit
from apps.livestock.services import create_lot_intake, register_exit, register_weighing

pytestmark = pytest.mark.django_db


def _boarding():
    return Client.objects.create(name="La Esperanza", kind=Client.Kind.BOARDING)


def _own():
    return Client.objects.create(name="Feedlot propio", kind=Client.Kind.OWN)


def _animal(client, ear_tag="A-001", weight="320"):
    return Animal.objects.create(
        client=client, ear_tag=ear_tag, category="steer", sex="male",
        entry_date="2026-01-10", entry_weight=Decimal(weight), current_weight=Decimal(weight),
    )


def _lot(client, head=50, total="16000"):
    _, lot = create_lot_intake(
        client=client, date="2026-01-10", code="L-01", head_count=head, total_weight=total
    )
    return lot


def _entries(client):
    return LedgerEntry.objects.filter(account=client.account)


# --- boarding: engorde commission (debit) ------------------------------------

def test_boarding_animal_sale_posts_engorde_commission_debit():
    client = _boarding()
    animal = _animal(client)
    register_weighing(animal=animal, weight="320", date="2026-02-01")
    register_weighing(animal=animal, weight="380", date="2026-04-02")  # +60 kg gained

    exit_event = register_exit(
        animal=animal, date="2026-06-01", kind=Exit.Kind.SALE,
        sale_price_per_kg="2400", commission_pct="10",
    )

    entry = _entries(client).get()
    # 10% × 60 kg × 2400 = 14400
    assert entry.direction == Direction.DEBIT
    assert entry.concept == Concept.SERVICE
    assert entry.amount == Decimal("14400.00")
    # The entry is traceable back to the exit (adr-49 rule 4).
    assert entry.source_kind == "exit"
    assert entry.source_id == exit_event.id
    # Historical snapshot: price and the kilos it was charged on (adr-25 rule 3).
    assert entry.unit_price == Decimal("2400.0000")
    assert entry.quantity == Decimal("60.000")


def test_boarding_commission_raises_the_client_balance():
    client = _boarding()
    animal = _animal(client)
    register_weighing(animal=animal, weight="320", date="2026-02-01")
    register_weighing(animal=animal, weight="380", date="2026-04-02")
    register_exit(
        animal=animal, date="2026-06-01", sale_price_per_kg="2400", commission_pct="10",
    )
    client.account.refresh_from_db()
    assert client.account.balance_cached == Decimal("14400.00")


def test_boarding_lot_commission_uses_per_head_kilos_gained():
    client = _boarding()
    lot = _lot(client, head=50, total="16000")
    register_weighing(lot=lot, weight="16000", date="2026-02-01", head_count=50)  # 320/head
    register_weighing(lot=lot, weight="17500", date="2026-03-03", head_count=50)  # 350/head
    # 30 kg/head × 50 head = 1500 kg gained; 5% × 1500 × 2400 = 180000
    register_exit(
        lot=lot, date="2026-06-01", head_count=50, weight="17500",
        sale_price_per_kg="2400", commission_pct="5",
    )
    entry = _entries(client).get()
    assert entry.amount == Decimal("180000.00")
    assert entry.quantity == Decimal("1500.000")


# --- own cattle: sale credit -------------------------------------------------

def test_own_animal_sale_posts_sale_credit():
    client = _own()
    animal = _animal(client)
    exit_event = register_exit(
        animal=animal, date="2026-06-01", kind=Exit.Kind.SALE,
        weight="400", sale_price_per_kg="2400",
    )
    entry = _entries(client).get()
    # 400 kg × 2400 = 960000, as a credit on the own account.
    assert entry.direction == Direction.CREDIT
    assert entry.concept == Concept.SALE
    assert entry.amount == Decimal("960000.00")
    assert entry.source_kind == "exit"
    assert entry.source_id == exit_event.id
    assert entry.unit_price == Decimal("2400.0000")
    assert entry.quantity == Decimal("400.000")


def test_own_sale_credit_lowers_the_own_account_balance():
    client = _own()
    animal = _animal(client)
    register_exit(animal=animal, date="2026-06-01", weight="400", sale_price_per_kg="2400")
    client.account.refresh_from_db()
    assert client.account.balance_cached == Decimal("-960000.00")


def test_own_sale_ignores_commission_pct():
    # Own cattle post the full produced value; a stray commission_pct is not applied.
    client = _own()
    animal = _animal(client)
    register_exit(
        animal=animal, date="2026-06-01", weight="400", sale_price_per_kg="2400",
        commission_pct="10",
    )
    entry = _entries(client).get()
    assert entry.concept == Concept.SALE
    assert entry.amount == Decimal("960000.00")


# --- honest cut: missing inputs post nothing ---------------------------------

def test_boarding_sale_without_price_posts_nothing():
    client = _boarding()
    animal = _animal(client)
    register_weighing(animal=animal, weight="320", date="2026-02-01")
    register_weighing(animal=animal, weight="380", date="2026-04-02")
    register_exit(animal=animal, date="2026-06-01", commission_pct="10")
    assert _entries(client).count() == 0


def test_boarding_sale_without_measurable_gain_posts_nothing():
    # A price and a percent, but no weighings to measure gain: nothing honest to charge.
    client = _boarding()
    animal = _animal(client)
    register_exit(
        animal=animal, date="2026-06-01", sale_price_per_kg="2400", commission_pct="10",
    )
    assert _entries(client).count() == 0


def test_own_sale_without_weight_posts_nothing():
    client = _own()
    animal = _animal(client)
    register_exit(animal=animal, date="2026-06-01", sale_price_per_kg="2400")
    assert _entries(client).count() == 0


def test_non_sale_exit_never_settles():
    # A transfer back to the client is not a sale, even with price and percent set.
    client = _boarding()
    animal = _animal(client)
    register_weighing(animal=animal, weight="320", date="2026-02-01")
    register_weighing(animal=animal, weight="380", date="2026-04-02")
    register_exit(
        animal=animal, date="2026-06-01", kind=Exit.Kind.TRANSFER,
        sale_price_per_kg="2400", commission_pct="10",
    )
    assert _entries(client).count() == 0


def test_exit_persists_commission_pct():
    client = _boarding()
    animal = _animal(client)
    exit_event = register_exit(
        animal=animal, date="2026-06-01", sale_price_per_kg="2400", commission_pct="7.5",
    )
    exit_event.refresh_from_db()
    assert exit_event.engorde_commission_pct == Decimal("7.500")
