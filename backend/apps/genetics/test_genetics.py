"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Genetics (adr-47): semen/embryo inventory by movement and the semen sale.

A SemenSale is the ONLY event that posts a ledger entry — a `sale` credit to the
own account (decision 4); every movement and flush posts none (decision 6). Stock
is DERIVED Σin − Σout (decision 2).
"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.clients.models import Client
from apps.ledger.models import Concept, Direction, LedgerEntry
from apps.livestock.models import Animal
from apps.genetics.models import (
    Direction as MoveDir,
    EmbryoBatch,
    EmbryoMovement,
    SemenBatch,
    SemenMovement,
    SemenReason,
    Sire,
)
from apps.genetics.services import (
    current_embryo_stock,
    current_semen_stock,
    register_embryo_flush,
    register_semen_movement,
    register_semen_sale,
)

pytestmark = pytest.mark.django_db


def _fixtures():
    own = Client.objects.create(name="Feedlot Propio", kind=Client.Kind.OWN)
    sire = Sire.objects.create(name="Toro Fuerte", breed="Angus")
    batch = SemenBatch.objects.create(
        sire=sire, batch_code="TF-001", unit_cost=Decimal("500")
    )
    return own, sire, batch


def test_semen_movement_derives_stock():
    _own, _sire, batch = _fixtures()
    register_semen_movement(
        semen_batch=batch, direction=MoveDir.IN, straws="20",
        reason=SemenReason.PURCHASE, date="2026-03-01",
    )
    register_semen_movement(
        semen_batch=batch, direction=MoveDir.OUT, straws="5",
        reason=SemenReason.INSEMINATION, date="2026-03-05",
    )
    assert current_semen_stock(semen_batch=batch) == Decimal("15")


def test_semen_movement_posts_no_ledger_entry():
    _own, _sire, batch = _fixtures()
    register_semen_movement(
        semen_batch=batch, direction=MoveDir.IN, straws="10",
        reason=SemenReason.PURCHASE, date="2026-03-01",
    )
    assert LedgerEntry.objects.count() == 0


def test_semen_movement_rejects_inactive_batch():
    _own, _sire, batch = _fixtures()
    batch.is_active = False
    batch.save()
    with pytest.raises(ValidationError):
        register_semen_movement(
            semen_batch=batch, direction=MoveDir.IN, straws="10",
            reason=SemenReason.PURCHASE, date="2026-03-01",
        )


def test_semen_movement_rejects_non_positive_quantity():
    _own, _sire, batch = _fixtures()
    with pytest.raises(ValidationError):
        register_semen_movement(
            semen_batch=batch, direction=MoveDir.IN, straws="0",
            reason=SemenReason.PURCHASE, date="2026-03-01",
        )


def test_semen_sale_credits_own_account_and_posts_out_movement():
    own, _sire, batch = _fixtures()
    register_semen_movement(
        semen_batch=batch, direction=MoveDir.IN, straws="20",
        reason=SemenReason.PURCHASE, date="2026-03-01",
    )
    sale = register_semen_sale(
        semen_batch=batch, straws="4", unit_price="1000",
        date="2026-03-10", buyer_name="Cabaña Vecina",
    )

    entry = LedgerEntry.objects.get(source_kind="semen_sale")
    assert entry.account == own.account
    assert entry.direction == Direction.CREDIT
    assert entry.concept == Concept.SALE
    assert entry.amount == Decimal("4000.00")
    assert entry.source_id == sale.id

    own.account.refresh_from_db()
    # A credit lowers the balance (positive balance = client owes; adr-25 r2).
    assert own.account.balance_cached == Decimal("-4000.00")

    out = SemenMovement.objects.get(reason=SemenReason.SALE)
    assert out.direction == MoveDir.OUT
    assert out.straws == Decimal("4")
    assert out.source_kind == "semen_sale"
    assert out.source_id == sale.id
    assert current_semen_stock(semen_batch=batch) == Decimal("16")


def test_semen_sale_rejects_insufficient_stock():
    _own, _sire, batch = _fixtures()
    register_semen_movement(
        semen_batch=batch, direction=MoveDir.IN, straws="2",
        reason=SemenReason.PURCHASE, date="2026-03-01",
    )
    with pytest.raises(ValidationError):
        register_semen_sale(
            semen_batch=batch, straws="5", unit_price="1000", date="2026-03-10",
        )
    assert LedgerEntry.objects.count() == 0


def test_semen_sale_locks_batch_before_stock_check():
    """#21 / #57: select_for_update on SemenBatch before check+movement."""
    _own, _sire, batch = _fixtures()
    register_semen_movement(
        semen_batch=batch, direction=MoveDir.IN, straws="10",
        reason=SemenReason.PURCHASE, date="2026-03-01",
    )
    with CaptureQueriesContext(connection) as ctx:
        register_semen_sale(
            semen_batch=batch, straws="1", unit_price="1000", date="2026-03-10",
        )
    sql = " ".join(q["sql"] for q in ctx.captured_queries).upper()
    assert "FOR UPDATE" in sql
    assert "GENETICS_SEMENBATCH" in sql.replace('"', "").replace("`", "")


def test_semen_sale_rejects_non_positive_price():
    _own, _sire, batch = _fixtures()
    register_semen_movement(
        semen_batch=batch, direction=MoveDir.IN, straws="10",
        reason=SemenReason.PURCHASE, date="2026-03-01",
    )
    with pytest.raises(ValidationError):
        register_semen_sale(
            semen_batch=batch, straws="1", unit_price="0", date="2026-03-10",
        )


def test_semen_sale_needs_an_own_account():
    # No Client(kind=own) exists → the sale cannot resolve a credit target.
    sire = Sire.objects.create(name="Toro Solo", breed="Angus")
    batch = SemenBatch.objects.create(sire=sire, batch_code="TS-001")
    register_semen_movement(
        semen_batch=batch, direction=MoveDir.IN, straws="10",
        reason=SemenReason.PURCHASE, date="2026-03-01",
    )
    with pytest.raises(ValidationError):
        register_semen_sale(
            semen_batch=batch, straws="1", unit_price="1000", date="2026-03-10",
        )


def test_embryo_flush_creates_batch_and_in_movement():
    own, sire, _batch = _fixtures()
    donor = Animal.objects.create(
        client=own, ear_tag="D-001", category="cow", entry_date="2026-01-10"
    )
    flush = register_embryo_flush(
        donor=donor, sire=sire, date="2026-03-01", embryos_collected="6", grade="A",
    )
    batch = EmbryoBatch.objects.get(donor=donor)
    assert batch.sire == sire
    movement = EmbryoMovement.objects.get(embryo_batch=batch)
    assert movement.direction == MoveDir.IN
    assert movement.quantity == Decimal("6")
    assert movement.source_kind == "embryo_flush"
    assert movement.source_id == flush.id
    assert current_embryo_stock(embryo_batch=batch) == Decimal("6")
    assert LedgerEntry.objects.count() == 0
