"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

"""Reference exchange rates (adr-39): ARS per one unit of a foreign currency.

An `FxRate` is a **reference** value for expressing metrics in another currency — never
the currency of the ledger, which stays ARS with a historical snapshot per movement
([[adr-25-account-ledger]] rule 3). Same immutability discipline as `market`: a row per
`(currency, date, source)` is idempotent — a re-entry updates it, never duplicates it.
"""

from django.db import models


class FxRate(models.Model):
    """One reference exchange rate: `rate` ARS per one unit of `currency` on a date."""

    currency = models.CharField(max_length=8)
    date = models.DateField()
    # ARS per one unit of `currency` (e.g. currency="USD", rate=1000 → 1 USD = 1000 ARS).
    rate = models.DecimalField(max_digits=18, decimal_places=6)
    source = models.CharField(max_length=40, default="manual")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "currency", "source"]
        constraints = [
            models.UniqueConstraint(
                fields=["currency", "date", "source"],
                name="unique_fx_rate_per_currency_date_source",
            )
        ]
        indexes = [models.Index(fields=["currency", "-date"])]

    def __str__(self):
        return f"{self.currency} {self.date}: {self.rate} ({self.source})"
