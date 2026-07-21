"""Client and Account models (docs/FEEDLOT.md, docs/FEEDLOT-DATA-MODEL.md).

A Client owns cattle — either a boarding third party or the feedlot's own
operation. Each Client has exactly one Account (its current account). The
account balance is DERIVED from the ledger (apps.ledger); `balance_cached` is
only a denormalized read cache (docs/adrs/adr-25-account-ledger.md rule 2).
"""

from decimal import Decimal

from django.db import models


class Client(models.Model):
    class Kind(models.TextChoices):
        BOARDING = "boarding", "Hotelería"
        OWN = "own", "Hacienda propia"

    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.BOARDING)
    tax_id = models.CharField(max_length=20, blank=True)
    contact = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Account(models.Model):
    client = models.OneToOneField(
        Client, on_delete=models.CASCADE, related_name="account"
    )
    # Denormalized read cache; positive = the client owes (debits - credits).
    # Source of truth is the sum of ledger entries (adr-25 rule 2).
    balance_cached = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Account<{self.client_id}>"
