"""Ledger posting service — the ONLY sanctioned way to write the account.

Entries are immutable (adr-25 rule 1): callers post new entries, they never
edit. `post_entry` keeps `Account.balance_cached` in step inside the same
transaction; `recompute_balance` rebuilds it from scratch (the cache is never
the source of truth, rule 2).
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.ledger.models import Concept, Direction, LedgerEntry, Payment


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
