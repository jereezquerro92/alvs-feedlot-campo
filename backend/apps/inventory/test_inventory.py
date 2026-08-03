"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Phase 10 (inventory): general input stock as movements (adr-37).

Stock is derived Σin − Σout, never stored. Nothing posts a ledger entry. An inactive
input type and a non-positive quantity are rejected in the service; a negative-driving
out is accepted (surfaced later, not blocked).
"""

from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.clients.models import Client
from apps.inventory.models import InputStockMovement, InputType, OwnerKind
from apps.inventory.services import current_stock, register_input_movement
from apps.ledger.models import LedgerEntry

pytestmark = pytest.mark.django_db


def _diesel():
    return InputType.objects.create(name="Gasoil", unit="l")


def test_stock_is_sum_of_movements():
    diesel = _diesel()
    register_input_movement(
        input_type=diesel, direction="in", quantity=Decimal("1000"), date=date(2026, 7, 1)
    )
    register_input_movement(
        input_type=diesel, direction="out", quantity=Decimal("250"), date=date(2026, 7, 3)
    )
    assert current_stock(input_type=diesel) == Decimal("750")


def test_movement_posts_no_ledger_entry():
    client = Client.objects.create(name="Don Aldo", kind=Client.Kind.BOARDING)
    diesel = _diesel()
    register_input_movement(
        input_type=diesel, direction="in", quantity=Decimal("100"),
        date=date(2026, 7, 1), owner_kind=OwnerKind.CLIENT, client=client,
    )
    assert LedgerEntry.objects.filter(account=client.account).count() == 0


def test_inactive_input_type_is_rejected():
    diesel = InputType.objects.create(name="Gasoil", unit="l", is_active=False)
    with pytest.raises(ValidationError):
        register_input_movement(
            input_type=diesel, direction="in", quantity=Decimal("100"), date=date(2026, 7, 1)
        )
    assert InputStockMovement.objects.count() == 0


def test_non_positive_quantity_is_rejected():
    diesel = _diesel()
    with pytest.raises(ValidationError):
        register_input_movement(
            input_type=diesel, direction="in", quantity=Decimal("0"), date=date(2026, 7, 1)
        )


def test_client_owner_requires_a_client():
    diesel = _diesel()
    with pytest.raises(ValidationError):
        register_input_movement(
            input_type=diesel, direction="in", quantity=Decimal("5"),
            date=date(2026, 7, 1), owner_kind=OwnerKind.CLIENT, client=None,
        )


def test_stock_is_scoped_by_owner_and_client():
    diesel = _diesel()
    client = Client.objects.create(name="Otro", kind=Client.Kind.BOARDING)
    register_input_movement(
        input_type=diesel, direction="in", quantity=Decimal("40"), date=date(2026, 7, 1)
    )
    register_input_movement(
        input_type=diesel, direction="in", quantity=Decimal("7"),
        date=date(2026, 7, 1), owner_kind=OwnerKind.CLIENT, client=client,
    )
    assert current_stock(input_type=diesel) == Decimal("40")
    assert current_stock(input_type=diesel, owner_kind=OwnerKind.CLIENT, client=client) == Decimal("7")


def test_over_consumption_is_not_blocked_but_shows_negative():
    diesel = _diesel()
    register_input_movement(
        input_type=diesel, direction="out", quantity=Decimal("30"), date=date(2026, 7, 1)
    )
    # Late/partial entry can drive stock negative — accepted, surfaced later, not blocked.
    assert current_stock(input_type=diesel) == Decimal("-30")
