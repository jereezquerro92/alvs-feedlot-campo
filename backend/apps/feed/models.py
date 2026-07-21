"""Feed: catalog, stock (as movements) and rations (docs/FEEDLOT-DATA-MODEL.md).

Stock is never a stored editable number — it is the sum of FeedStockMovement
rows, per (owner_kind, client, feed_type). A FeedingEvent's `origin` decides
the costing (adr-25 rule 4): own_stock charges the client; client_stock does not.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models


class OwnerKind(models.TextChoices):
    OWN = "own", "Feedlot (propio)"
    CLIENT = "client", "Cliente"


class FeedType(models.Model):
    name = models.CharField(max_length=120, unique=True)
    unit = models.CharField(max_length=16, default="kg")
    category = models.CharField(max_length=60, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class FeedDelivery(models.Model):
    """Feed the client provides — increases the client's stock."""

    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="feed_deliveries")
    feed_type = models.ForeignKey(FeedType, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Delivery {self.feed_type_id} {self.quantity}"


class FeedStockMovement(models.Model):
    class Direction(models.TextChoices):
        IN = "in", "Entrada"
        OUT = "out", "Salida"

    owner_kind = models.CharField(max_length=8, choices=OwnerKind.choices)
    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, null=True, blank=True, related_name="feed_stock"
    )
    feed_type = models.ForeignKey(FeedType, on_delete=models.PROTECT)
    direction = models.CharField(max_length=3, choices=Direction.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    source_kind = models.CharField(max_length=32, blank=True)
    source_id = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["owner_kind", "client", "feed_type"])]

    def __str__(self):
        return f"{self.direction} {self.quantity} {self.feed_type_id}"


class FeedingEvent(models.Model):
    class Origin(models.TextChoices):
        CLIENT_STOCK = "client_stock", "Stock del cliente"
        OWN_STOCK = "own_stock", "Stock propio (feedlot)"

    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="feedings")
    animal = models.ForeignKey(
        "livestock.Animal", on_delete=models.PROTECT, null=True, blank=True, related_name="feedings"
    )
    lot = models.ForeignKey(
        "livestock.Lot", on_delete=models.PROTECT, null=True, blank=True, related_name="feedings"
    )
    feed_type = models.ForeignKey(FeedType, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=14, decimal_places=4)
    origin = models.CharField(max_length=12, choices=Origin.choices)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        constraints = [
            # A feeding targets an animal OR a lot — exactly one (adr-26 rule 3).
            models.CheckConstraint(
                name="feeding_target_animal_xor_lot",
                condition=(
                    models.Q(animal__isnull=False, lot__isnull=True)
                    | models.Q(animal__isnull=True, lot__isnull=False)
                ),
            )
        ]

    @property
    def total_cost(self):
        return (self.quantity or Decimal("0")) * (self.unit_price or Decimal("0"))

    def __str__(self):
        return f"Feeding {self.date} {self.feed_type_id} {self.quantity}"
