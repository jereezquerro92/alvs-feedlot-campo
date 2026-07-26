"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Ledger posting service — the ONLY sanctioned way to write the account.

Entries are immutable (adr-25 rule 1): callers post new entries, they never
edit. `post_entry` keeps `Account.balance_cached` in step inside the same
transaction; `recompute_balance` rebuilds it from scratch (the cache is never
the source of truth, rule 2).
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.ledger.models import (
    Concept,
    Direction,
    LedgerEntry,
    Payment,
    PaymentAllocation,
)


def recompute_balance(account):
    """Derive the balance from the entries: sum(debits) - sum(credits)."""
    agg = LedgerEntry.objects.filter(account=account).values("direction").annotate(
        total=Sum("amount")
    )
    totals = {row["direction"]: row["total"] or Decimal("0") for row in agg}
    balance = totals.get(Direction.DEBIT, Decimal("0")) - totals.get(
        Direction.CREDIT, Decimal("0")
    )
    return balance


@transaction.atomic
def post_entry(
    *,
    account,
    direction,
    amount,
    concept,
    date,
    source_kind="",
    source_id=None,
    unit_price=None,
    quantity=None,
    description="",
    created_by=None,
):
    """Append one immutable entry and update the cached balance atomically."""
    amount = Decimal(amount)
    entry = LedgerEntry.objects.create(
        account=account,
        date=date,
        direction=direction,
        amount=amount,
        concept=concept,
        source_kind=source_kind,
        source_id=source_id,
        unit_price=unit_price,
        quantity=quantity,
        description=description,
        created_by=created_by,
    )
    delta = amount if direction == Direction.DEBIT else -amount
    account.balance_cached = (account.balance_cached or Decimal("0")) + delta
    account.save(update_fields=["balance_cached", "updated_at"])
    return entry


@transaction.atomic
def register_payment(*, account, amount, date, method="transfer", reference="", created_by=None):
    """Register a payment: a credit entry plus its Payment record (adr-25 rule 7)."""
    entry = post_entry(
        account=account,
        direction=Direction.CREDIT,
        amount=amount,
        concept=Concept.PAYMENT,
        date=date,
        source_kind="payment",
        description=f"Pago {method} {reference}".strip(),
        created_by=created_by,
    )
    payment = Payment.objects.create(
        account=account,
        date=date,
        amount=Decimal(amount),
        method=method,
        reference=reference,
        entry=entry,
        created_by=created_by,
    )
    entry.source_id = payment.id
    entry.save(update_fields=["source_id"])
    return payment


# --- payment-to-charge imputation (adr-41) ---------------------------------


def _allocated_for_payment(payment):
    """Sum already imputed from this payment."""
    total = PaymentAllocation.objects.filter(payment=payment).aggregate(
        s=Sum("amount")
    )["s"]
    return total or Decimal("0")


def _allocated_for_entry(entry):
    """Sum already imputed against this debit, across all payments."""
    total = PaymentAllocation.objects.filter(entry=entry).aggregate(
        s=Sum("amount")
    )["s"]
    return total or Decimal("0")


def outstanding_charges(account):
    """Per-debit imputation state, derived — never a stored field (adr-41 dec 4).

    Returns one dict per debit entry of the account (oldest first) with:
    `entry`, `date`, `concept`, `amount`, `allocated` (Σ PaymentAllocation),
    `outstanding` (`amount` − allocated).
    """
    debits = LedgerEntry.objects.filter(
        account=account, direction=Direction.DEBIT
    ).order_by("date", "id")
    allocated = {
        row["entry_id"]: (row["total"] or Decimal("0"))
        for row in PaymentAllocation.objects.filter(entry__account=account)
        .values("entry_id")
        .annotate(total=Sum("amount"))
    }
    charges = []
    for entry in debits:
        a = allocated.get(entry.id, Decimal("0"))
        charges.append(
            {
                "entry": entry.id,
                "date": entry.date,
                "concept": entry.concept,
                "amount": entry.amount,
                "allocated": a,
                "outstanding": entry.amount - a,
            }
        )
    return charges


def _fifo_allocations(payment):
    """Auto-imputation lines: oldest unpaid debit first (adr-41 decision 3)."""
    remaining = Decimal(payment.amount) - _allocated_for_payment(payment)
    lines = []
    for charge in outstanding_charges(payment.account):
        if remaining <= 0:
            break
        outstanding = charge["outstanding"]
        if outstanding <= 0:
            continue
        take = min(outstanding, remaining)
        lines.append({"entry": charge["entry"], "amount": take})
        remaining -= take
    return lines


@transaction.atomic
def impute_payment(*, payment, allocations=None, auto=False, created_by=None):
    """Impute a payment against debit charges (adr-41).

    `allocations`: iterable of {"entry": LedgerEntry|id, "amount": <decimal-ish>}.
    When omitted (or empty) and `auto=True`, imputes FIFO oldest-charge-first.
    Creates PaymentAllocation rows; posts NO ledger entry and moves NO balance —
    the total already moved when the payment posted its credit (decision 1).
    Validates in the service (decision 2): each entry is a debit of the payment's
    own account, amount is positive, and neither the payment nor any debit is
    over-allocated. Raises ValueError on any violation (the whole call rolls back).
    """
    if not allocations:
        if not auto:
            raise ValueError("no allocations given and auto is False")
        allocations = _fifo_allocations(payment)

    # Resolve, validate, and accumulate per-payment / per-entry running totals so
    # a multi-line call cannot over-allocate within itself.
    payment_running = _allocated_for_payment(payment)
    payment_amount = Decimal(payment.amount)
    entry_running = {}
    created = []
    for line in allocations:
        raw_entry = line["entry"]
        entry = (
            raw_entry
            if isinstance(raw_entry, LedgerEntry)
            else LedgerEntry.objects.filter(pk=raw_entry).first()
        )
        if entry is None:
            raise ValueError(f"ledger entry {raw_entry} does not exist")
        amount = Decimal(str(line["amount"]))
        if amount <= 0:
            raise ValueError("allocation amount must be positive")
        if entry.account_id != payment.account_id:
            raise ValueError("entry belongs to a different account than the payment")
        if entry.direction != Direction.DEBIT:
            raise ValueError("a payment can only be imputed against a debit charge")

        payment_running += amount
        if payment_running > payment_amount:
            raise ValueError("allocations exceed the payment amount")

        already = entry_running.get(entry.id)
        if already is None:
            already = _allocated_for_entry(entry)
        already += amount
        if already > entry.amount:
            raise ValueError("allocations exceed the charge amount")
        entry_running[entry.id] = already

        created.append(
            PaymentAllocation(
                payment=payment, entry=entry, amount=amount, created_by=created_by
            )
        )

    return [PaymentAllocation.objects.create(
        payment=obj.payment, entry=obj.entry, amount=obj.amount, created_by=obj.created_by
    ) for obj in created]
