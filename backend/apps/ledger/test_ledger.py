from decimal import Decimal

import pytest

from apps.clients.models import Client
from apps.ledger.models import Concept, Direction, LedgerEntry, Payment
from apps.ledger.services import post_entry, recompute_balance, register_payment

pytestmark = pytest.mark.django_db


def _account():
    return Client.objects.create(name="Cliente").account


def test_account_created_with_client():
    client = Client.objects.create(name="Auto")
    assert client.account is not None
    assert client.account.balance_cached == Decimal("0.00")


def test_debit_and_credit_move_balance():
    account = _account()
    post_entry(account=account, direction=Direction.DEBIT, amount="1000",
               concept=Concept.FEEDING, date="2026-07-01")
    post_entry(account=account, direction=Direction.CREDIT, amount="300",
               concept=Concept.ADJUSTMENT, date="2026-07-02")
    account.refresh_from_db()
    assert account.balance_cached == Decimal("700.00")
    # Cache matches the derived truth (adr-25 rule 2).
    assert recompute_balance(account) == Decimal("700.00")


def test_payment_creates_credit_entry():
    account = _account()
    post_entry(account=account, direction=Direction.DEBIT, amount="5000",
               concept=Concept.FEEDING, date="2026-07-01")
    payment = register_payment(account=account, amount="2000", date="2026-07-05", method="transfer")
    assert isinstance(payment, Payment)
    assert payment.entry.direction == Direction.CREDIT
    assert payment.entry.concept == Concept.PAYMENT
    account.refresh_from_db()
    assert account.balance_cached == Decimal("3000.00")


def test_correction_is_a_counter_entry_not_an_edit():
    account = _account()
    original = post_entry(account=account, direction=Direction.DEBIT, amount="1000",
                          concept=Concept.FEEDING, date="2026-07-01")
    # Correct by posting the inverse, never editing `original`.
    post_entry(account=account, direction=Direction.CREDIT, amount="1000",
               concept=Concept.ADJUSTMENT, date="2026-07-03", description="contra-asiento")
    account.refresh_from_db()
    assert account.balance_cached == Decimal("0.00")
    assert LedgerEntry.objects.filter(account=account).count() == 2
    original.refresh_from_db()
    assert original.amount == Decimal("1000.00")  # untouched
