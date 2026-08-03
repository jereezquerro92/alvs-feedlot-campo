"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext

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


def test_post_entry_updates_balance_via_f_expression():
    """#5 / #57: F() update leaves the in-memory instance stale until refresh."""
    account = _account()
    assert account.balance_cached == Decimal("0.00")
    with CaptureQueriesContext(connection) as ctx:
        post_entry(
            account=account,
            direction=Direction.DEBIT,
            amount="1000",
            concept=Concept.FEEDING,
            date="2026-07-01",
        )
    # In-memory cache is not Python-RMW'd — callers must refresh.
    assert account.balance_cached == Decimal("0.00")
    account.refresh_from_db()
    assert account.balance_cached == Decimal("1000.00")
    sql = " ".join(q["sql"] for q in ctx.captured_queries).upper()
    assert "BALANCE_CACHED" in sql
    # F("balance_cached") + delta renders as column self-reference in UPDATE.
    assert sql.count("BALANCE_CACHED") >= 2


def test_recompute_balances_command_repairs_drifted_cache():
    """#14 / #57: operational entrypoint for recompute_balance."""
    account = _account()
    post_entry(
        account=account,
        direction=Direction.DEBIT,
        amount="2500",
        concept=Concept.FEEDING,
        date="2026-07-01",
    )
    account.balance_cached = Decimal("999.00")
    account.save(update_fields=["balance_cached"])
    call_command("recompute_balances", account=account.pk)
    account.refresh_from_db()
    assert account.balance_cached == Decimal("2500.00")
    assert account.balance_cached == recompute_balance(account)


@pytest.mark.parametrize("amount", ["0", "-100"])
def test_register_payment_rejects_non_positive_amount(amount):
    account = _account()
    with pytest.raises(ValidationError):
        register_payment(account=account, amount=amount, date="2026-07-05")
    assert Payment.objects.filter(account=account).count() == 0
    assert LedgerEntry.objects.filter(account=account).count() == 0
