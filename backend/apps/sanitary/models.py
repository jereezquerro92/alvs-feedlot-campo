"""Animal health — catalogue and applications (Phase 2).

Named `sanitary`, not `health`: the template already owns an app called `health`
for the liveness probe. Same shape as `feed` minus the stock ledger — health
products are always the feedlot's, so every application is billed (there is no
client-supplied equivalent). Stock of vaccines is deliberately out of scope for
this phase (docs/feedlot/11-plan-de-fases.md, decision 3).
"""

from decimal import Decimal

from django.conf import settings
from django.db import models


class HealthProduct(models.Model):
    """Catalogue row. Editable: `unit_price` is the price from here on out —
    past applications keep their own snapshot and are never rewritten."""

    class Kind(models.TextChoices):
        VACCINE = "vaccine", "Vacuna"
        TREATMENT = "treatment", "Tratamiento"
        ANTIPARASITIC = "antiparasitic", "Antiparasitario"
        OTHER = "other", "Otro"

    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=14, choices=Kind.choices, default=Kind.VACCINE)
    unit = models.CharField(max_length=20, default="dosis")
    unit_price = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class HealthEvent(models.Model):
    """An application. Immutable, always billed."""

    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="health_events"
    )
    animal = models.ForeignKey(
        "livestock.Animal", on_delete=models.PROTECT, null=True, blank=True,
        related_name="health_events",
    )
    lot = models.ForeignKey(
        "livestock.Lot", on_delete=models.PROTECT, null=True, blank=True,
        related_name="health_events",
    )
    product = models.ForeignKey(HealthProduct, on_delete=models.PROTECT, related_name="events")
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    head_count = models.PositiveIntegerField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=14, decimal_places=4)
    date = models.DateField()
    applied_by = models.CharField(max_length=120, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["client", "date"])]
        constraints = [
            models.CheckConstraint(
                name="health_event_target_animal_xor_lot",
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
        return f"Health {self.date} {self.product_id} x{self.quantity}"
