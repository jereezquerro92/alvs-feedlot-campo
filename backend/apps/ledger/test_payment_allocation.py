"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Payment-to-charge imputation (docs/adrs/adr-41-payment-allocation.md).

Imputing a payment classifies an already-posted credit against specific debit
charges. It creates PaymentAllocation rows and must NEVER move the balance nor
mutate a LedgerEntry (adr-41 decision 1); the total balance already moved when
the payment posted its credit.
"""

from decimal import Decimal

import pytest

from apps.clients.models import Client
from apps.ledger.models import Concept, Direction, LedgerEntry, PaymentAllocation
from apps.ledger.services import (
    impute_payment,
    outstanding_charges,
    post_entry,
    register_payment,
)

pytestmark = pytest.mark.django_db


def _account():
    return Client.objects.create(name="Cliente").account


def _debit(account, amount, date, concept=Concept.FEEDING):
    return post_entry(
        account=account, direction=Direction.DEBIT, amount=amount,
        concept=concept, date=date,
    )


# --- decision 1: imputing never moves the balance nor mutates entries ---

def test_explicit_imputation_creates_allocations_without_moving_balance():
    account = _account()
    d1 = _debit(account, "1000", "2026-07-01")
    payment = register_payment(account=account, amount="600", date="2026-07-05")
    account.refresh_from_db()
    balance_before = account.balance_cached  # 1000 - 600 = 400

    allocs = impute_payment(payment=payment, allocations=[{"entry": d1.id, "amount": "600"}])

    assert len(allocs) == 1
    assert isinstance(allocs[0], PaymentAllocation)
    assert allocs[0].payment_id == payment.id
    assert allocs[0].entry_id == d1.id
    assert allocs[0].amount == Decimal("600.00")
    account.refresh_from_db()
    assert account.balance_cached == balance_before  # imputing moved nothing
    d1.refresh_from_db()
    assert d1.amount == Decimal("1000.00")  # entry untouched (adr-25 rule 1)


# --- decision 2: validation, no over-allocation ---

def test_over_allocating_a_payment_is_rejected():
    account = _account()
    d1 = _debit(account, "1000", "2026-07-01")
    payment = register_payment(account=account, amount="500", date="2026-07-05")
    with pytest.raises(ValueError):
        impute_payment(payment=payment, allocations=[{"entry": d1.id, "amount": "600"}])
    assert PaymentAllocation.objects.count() == 0


def test_over_allocating_a_debit_is_rejected():
    account = _account()
    d1 = _debit(account, "300", "2026-07-01")
    payment = register_payment(account=account, amount="1000", date="2026-07-05")
    with pytest.raises(ValueError):
        impute_payment(payment=payment, allocations=[{"entry": d1.id, "amount": "400"}])
    assert PaymentAllocation.objects.count() == 0


def test_cannot_impute_against_a_credit_entry():
    account = _account()
    payment = register_payment(account=account, amount="500", date="2026-07-05")
    with pytest.raises(ValueError):
        impute_payment(payment=payment, allocations=[{"entry": payment.entry_id, "amount": "100"}])


def test_cannot_impute_across_accounts():
    a1 = _account()
    a2 = _account()
    d_other = _debit(a2, "1000", "2026-07-01")
    payment = register_payment(account=a1, amount="500", date="2026-07-05")
    with pytest.raises(ValueError):
        impute_payment(payment=payment, allocations=[{"entry": d_other.id, "amount": "100"}])


def test_non_positive_allocation_is_rejected():
    account = _account()
    d1 = _debit(account, "1000", "2026-07-01")
    payment = register_payment(account=account, amount="500", date="2026-07-05")
    with pytest.raises(ValueError):
        impute_payment(payment=payment, allocations=[{"entry": d1.id, "amount": "0"}])


# --- decision 3: FIFO auto-imputation, oldest charge first ---

def test_auto_fifo_imputes_oldest_charge_first():
    account = _account()
    d1 = _debit(account, "400", "2026-07-01")
    d2 = _debit(account, "400", "2026-07-10")
    payment = register_payment(account=account, amount="600", date="2026-07-15")

    allocs = impute_payment(payment=payment, auto=True)

    by_entry = {a.entry_id: a.amount for a in allocs}
    assert by_entry[d1.id] == Decimal("400.00")  # oldest fully covered
    assert by_entry[d2.id] == Decimal("200.00")  # remainder to the next
    assert sum(by_entry.values()) == Decimal("600.00")  # never exceeds the payment


def test_auto_fifo_stops_when_payment_exhausted():
    account = _account()
    d1 = _debit(account, "1000", "2026-07-01")
    _debit(account, "1000", "2026-07-10")
    payment = register_payment(account=account, amount="300", date="2026-07-15")

    allocs = impute_payment(payment=payment, auto=True)

    assert len(allocs) == 1
    assert allocs[0].entry_id == d1.id
    assert allocs[0].amount == Decimal("300.00")


def test_auto_fifo_skips_already_allocated_portion():
    account = _account()
    d1 = _debit(account, "500", "2026-07-01")
    d2 = _debit(account, "500", "2026-07-10")
    p1 = register_payment(account=account, amount="500", date="2026-07-05")
    impute_payment(payment=p1, auto=True)  # fully covers d1

    p2 = register_payment(account=account, amount="500", date="2026-07-20")
    allocs = impute_payment(payment=p2, auto=True)  # should go to d2, not d1

    assert len(allocs) == 1
    assert allocs[0].entry_id == d2.id
    assert allocs[0].amount == Decimal("500.00")


# --- decision 4: outstanding is derived, never stored ---

def test_outstanding_charges_derives_allocated_and_remaining():
    account = _account()
    d1 = _debit(account, "1000", "2026-07-01")
    d2 = _debit(account, "500", "2026-07-10")
    payment = register_payment(account=account, amount="700", date="2026-07-15")
    impute_payment(payment=payment, allocations=[{"entry": d1.id, "amount": "700"}])

    charges = {c["entry"]: c for c in outstanding_charges(account)}

    assert charges[d1.id]["allocated"] == Decimal("700.00")
    assert charges[d1.id]["outstanding"] == Decimal("300.00")
    assert charges[d2.id]["allocated"] == Decimal("0.00")
    assert charges[d2.id]["outstanding"] == Decimal("500.00")


def test_outstanding_ignores_credit_entries():
    account = _account()
    _debit(account, "1000", "2026-07-01")
    register_payment(account=account, amount="400", date="2026-07-05")
    charges = outstanding_charges(account)
    # Only the debit is a charge; the payment credit is not listed.
    assert len(charges) == 1
    assert charges[0]["concept"] == Concept.FEEDING
