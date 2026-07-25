"""General input inventory (adr-37): non-feed supplies as stock movements.

Generalises the feed-stock pattern (adr-25 rule 4) to inputs that are not feed —
diesel, posts, wire, field sanitary. Stock is never a stored editable number: it is
the sum of `InputStockMovement` rows per `(owner_kind, client, input_type)`. Nothing
here posts a ledger entry (decision 3); `unit_price` is informational only.
"""

from django.conf import settings
from django.db import models


class OwnerKind(models.TextChoices):
    OWN = "own", "Feedlot (propio)"
    CLIENT = "client", "Cliente"


class InputType(models.Model):
    """Editable catalog of a general input — diesel, posts, wire, sanitary…"""

    name = models.CharField(max_length=120, unique=True)
    unit = models.CharField(max_length=16, default="unit")
    category = models.CharField(max_length=60, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class InputStockMovement(models.Model):
    """An immutable in/out movement of an input. Stock is derived, never stored."""

    class Direction(models.TextChoices):
        IN = "in", "Entrada"
        OUT = "out", "Salida"

    owner_kind = models.CharField(
        max_length=8, choices=OwnerKind.choices, default=OwnerKind.OWN
    )
    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, null=True, blank=True,
        related_name="input_stock",
    )
    input_type = models.ForeignKey(InputType, on_delete=models.PROTECT)
    direction = models.CharField(max_length=3, choices=Direction.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    # Informational purchase price for stock valuation — never a ledger charge (decision 3).
    unit_price = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    date = models.DateField()
    note = models.CharField(max_length=255, blank=True)
    # Generic seam for a future link to an originating event (adr-24 rule 4).
    source_kind = models.CharField(max_length=32, blank=True)
    source_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["owner_kind", "client", "input_type"])]

    def __str__(self):
        return f"{self.direction} {self.quantity} {self.input_type_id}"
