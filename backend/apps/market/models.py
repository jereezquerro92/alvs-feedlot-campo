"""Reference cattle prices (Phase 4, docs/feedlot/06-precios-hacienda.md).

These are **reference** values for metrics and the financial advisor — never the
currency of the ledger, which stays ARS with a historical snapshot per movement.

Same immutability discipline as the rest of the system: a price row for a given
(source, category, date) is written once. A correction is a re-ingest of that
row's payload, not an edit of a different number. `raw` keeps the source payload
so the parse can be redone without hitting the source again.

MarketPrice carries min/max/avg/median/head — not just the average — because the
sources publish all of them (docs/feedlot/06b) and throwing them away loses signal
the advisor could use.
"""

from django.db import models


class MarketSource(models.Model):
    """A price origin. `slug` selects the connector; `manual` needs no connector."""

    class Kind(models.TextChoices):
        MARKET = "market", "Mercado físico"
        INDEX = "index", "Índice"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=40, unique=True)
    kind = models.CharField(max_length=8, choices=Kind.choices, default=Kind.MARKET)
    is_active = models.BooleanField(default=True)
    # False for `manual`: the ingest command skips sources with no connector.
    is_automated = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class MarketPrice(models.Model):
    """One category's prices from one source on one date. Idempotent by that triple."""

    source = models.ForeignKey(MarketSource, on_delete=models.PROTECT, related_name="prices")
    category = models.CharField(max_length=60)
    date = models.DateField()

    # ARS per kg. `price_avg` is the headline; the rest are kept when the source gives them.
    price_avg = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    price_min = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    price_max = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    price_median = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    head_count = models.PositiveIntegerField(null=True, blank=True)
    raw = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "source", "category"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "category", "date"], name="unique_price_per_source_category_date"
            )
        ]
        indexes = [models.Index(fields=["source", "date"])]

    def __str__(self):
        return f"{self.source_id} {self.category} {self.date}: {self.price_avg}"
