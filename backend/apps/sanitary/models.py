"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

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


class SanitaryPlan(models.Model):
    """A reusable, editable template of scheduled sanitary applications (adr-40
    decision 1). Holds no dates itself — its items are relative day offsets."""

    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SanitaryPlanItem(models.Model):
    """One scheduled dose within a plan: a product due `day_offset` days after the
    enrollment's start date (adr-40 decision 2). Editable catalog line."""

    plan = models.ForeignKey(SanitaryPlan, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        HealthProduct, on_delete=models.PROTECT, related_name="plan_items"
    )
    day_offset = models.PositiveIntegerField(default=0)
    dose = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("1"))
    notes = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["day_offset", "id"]

    def __str__(self):
        return f"{self.plan_id} +{self.day_offset}d {self.product_id}"


class PlanEnrollment(models.Model):
    """An immutable event: a target (animal XOR lot) starts a plan on a date (adr-40
    decision 1). Posts no ledger entry — billing stays with HealthEvent (decision 4)."""

    plan = models.ForeignKey(
        SanitaryPlan, on_delete=models.PROTECT, related_name="enrollments"
    )
    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="plan_enrollments"
    )
    animal = models.ForeignKey(
        "livestock.Animal", on_delete=models.PROTECT, null=True, blank=True,
        related_name="plan_enrollments",
    )
    lot = models.ForeignKey(
        "livestock.Lot", on_delete=models.PROTECT, null=True, blank=True,
        related_name="plan_enrollments",
    )
    start_date = models.DateField()
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-start_date", "-id"]
        indexes = [models.Index(fields=["client", "start_date"])]
        constraints = [
            models.CheckConstraint(
                name="plan_enrollment_target_animal_xor_lot",
                condition=(
                    models.Q(animal__isnull=False, lot__isnull=True)
                    | models.Q(animal__isnull=True, lot__isnull=False)
                ),
            )
        ]

    def __str__(self):
        return f"Enrollment {self.plan_id} {self.start_date}"
