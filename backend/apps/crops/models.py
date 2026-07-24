"""Crops rubro: pivots, plantings, cuttings, field tasks (adr-32-multi-rubro-assets).

`Pivot` is a concrete `AssetBase` (a center-pivot circle). `Crop` is a planting on
it. `Cutting` is an immutable harvest event that posts NO ledger entry — it is
production, not a delivered input (adr-32 decision 4). `FieldTask` is a chargeable
`CostedEvent` that posts a `service` debit through the ledger's generic seam
(adr-32 decisions 3, 5). English choices; Spanish only in rendered output.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.assets.models import AssetBase, CostedEvent


class Pivot(AssetBase):
    """A center-pivot irrigation circle (círculo). Editable catalog (adr-32 decision 6)."""

    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="pivots"
    )
    area_ha = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))

    class Meta:
        ordering = ["client", "name"]


class Crop(models.Model):
    """A planting standing on a pivot. Editable catalog."""

    class Species(models.TextChoices):
        ALFALFA = "alfalfa", "Alfalfa"
        OTHER = "other", "Otro"

    class Status(models.TextChoices):
        ACTIVE = "active", "Activo"
        TERMINATED = "terminated", "Terminado"

    pivot = models.ForeignKey(Pivot, on_delete=models.PROTECT, related_name="crops")
    species = models.CharField(
        max_length=12, choices=Species.choices, default=Species.ALFALFA
    )
    sown_date = models.DateField()
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.ACTIVE
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sown_date", "-id"]

    def __str__(self):
        return f"{self.species} @ pivot {self.pivot_id}"


class Cutting(models.Model):
    """A harvest event (corte). Immutable; posts no ledger entry (adr-32 decision 4)."""

    class Quality(models.TextChoices):
        HIGH = "high", "Alta"
        MEDIUM = "medium", "Media"
        LOW = "low", "Baja"

    crop = models.ForeignKey(Crop, on_delete=models.PROTECT, related_name="cuttings")
    date = models.DateField()
    kg_harvested = models.DecimalField(max_digits=12, decimal_places=2)
    bales = models.PositiveIntegerField(null=True, blank=True)
    quality = models.CharField(max_length=8, choices=Quality.choices, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["crop", "date"])]

    def __str__(self):
        return f"Cutting {self.date} crop={self.crop_id} {self.kg_harvested}kg"


class FieldTask(CostedEvent):
    """Labor on a pivot (tarea). Posts a `service` debit (adr-32 decisions 3, 5)."""

    class Category(models.TextChoices):
        SOWING = "sowing", "Siembra"
        FERTILIZING = "fertilizing", "Fertilización"
        IRRIGATION = "irrigation", "Riego"
        WEEDING = "weeding", "Control de malezas"
        OTHER = "other", "Otro"

    pivot = models.ForeignKey(Pivot, on_delete=models.PROTECT, related_name="field_tasks")
    title = models.CharField(max_length=120)
    category = models.CharField(
        max_length=12, choices=Category.choices, default=Category.OTHER
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["client", "date"]),
            models.Index(fields=["pivot", "date"]),
        ]

    def __str__(self):
        return f"FieldTask {self.date} {self.title}"
