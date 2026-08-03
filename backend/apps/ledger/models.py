"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

"""Current-account ledger (docs/adrs/adr-25-account-ledger.md).

The account is an immutable ledger of LedgerEntry rows: never edited, never
deleted; a mistake is corrected by a new counter-entry. Balance is derived as
sum(debits) - sum(credits); positive means the client owes. Every charge
snapshots its unit_price/quantity (historical price) and links back to the
event that produced it via (source_kind, source_id) — the generic costing seam
(adr-49 rule 4) that lets any future domain post charges without touching this app.
"""

from django.conf import settings
from django.db import models


class Concept(models.TextChoices):
    FEEDING = "feeding", "Alimentación"
    HEALTH = "health", "Sanidad"
    SERVICE = "service", "Servicio"
    ADJUSTMENT = "adjustment", "Ajuste"
    PAYMENT = "payment", "Pago"
    SALE = "sale", "Venta"  # own-cattle sale credit (adr-43)


class Direction(models.TextChoices):
    DEBIT = "debit", "Débito"
    CREDIT = "credit", "Crédito"


class LedgerEntry(models.Model):
    account = models.ForeignKey(
        "clients.Account", on_delete=models.PROTECT, related_name="entries"
    )
    date = models.DateField()
    direction = models.CharField(max_length=6, choices=Direction.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    concept = models.CharField(max_length=16, choices=Concept.choices)
    # Generic link to the originating event (adr-49 rule 4). Never a per-domain FK.
    source_kind = models.CharField(max_length=32, blank=True)
    source_id = models.PositiveBigIntegerField(null=True, blank=True)
    # Historical snapshot for traceability (adr-25 rule 3).
    unit_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["account", "date"])]

    def __str__(self):
        sign = "-" if self.direction == Direction.DEBIT else "+"
        return f"{self.date} {sign}{self.amount} ({self.concept})"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Efectivo"
        TRANSFER = "transfer", "Transferencia"
        CHECK = "check", "Cheque"
        OTHER = "other", "Otro"

    account = models.ForeignKey(
        "clients.Account", on_delete=models.PROTECT, related_name="payments"
    )
    date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    method = models.CharField(max_length=16, choices=Method.choices, default=Method.TRANSFER)
    reference = models.CharField(max_length=120, blank=True)
    # The credit entry this payment produced (adr-25 rule 7).
    entry = models.OneToOneField(
        LedgerEntry, on_delete=models.PROTECT, null=True, blank=True, related_name="payment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"Payment {self.date} {self.amount}"


class PaymentAllocation(models.Model):
    """Imputation of a payment against a specific debit charge (adr-41).

    An immutable annotation linking a Payment to a debit LedgerEntry with an
    amount. It is NOT a LedgerEntry: it posts nothing to the ledger and moves no
    balance — the total balance already moved when the payment posted its credit
    (adr-25 rule 7, adr-41 decision 1). No LedgerEntry is ever mutated.
    """

    payment = models.ForeignKey(
        Payment, on_delete=models.PROTECT, related_name="allocations"
    )
    # The debit entry this payment portion settles.
    entry = models.ForeignKey(
        LedgerEntry, on_delete=models.PROTECT, related_name="allocations"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["payment"]),
            models.Index(fields=["entry"]),
        ]

    def __str__(self):
        return f"Alloc payment={self.payment_id} entry={self.entry_id} {self.amount}"
