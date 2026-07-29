"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

"""Breeding: the reproductive cycle service → tacto → parición → destete (adr-46).

Service, PregnancyCheck, Calving and Weaning are immutable dated events sharing
the LifecycleEvent shape (adr-28 decision 1): each targets one Animal XOR one Lot
(adr-26 rule 3) with its own uniquely-named CHECK constraint. IatfProtocol and
IatfProtocolStep are editable templates whose step dates are DERIVED from the
Service date, never stored (adr-40 decisions 1-2, adr-46 decision 5). Reproductive
status and genealogy are DERIVED from the events, never stored fields (decision 3).
"""

from datetime import timedelta

from django.db import models

from apps.livestock.models import LifecycleEvent


GESTATION_DAYS = 280  # bovine, for the derived estimated-calving date (not stored).


class Method(models.TextChoices):
    NATURAL = "natural", "Servicio natural"
    AI = "ai", "Inseminación artificial"
    IATF = "iatf", "IATF"
    EMBRYO_TRANSFER = "embryo_transfer", "Transferencia embrionaria"


class PregnancyMethod(models.TextChoices):
    PALPATION = "palpation", "Palpación"
    ULTRASOUND = "ultrasound", "Ecografía"
    BLOOD = "blood", "Sangre"


class PregnancyResult(models.TextChoices):
    PREGNANT = "pregnant", "Preñada"
    EMPTY = "empty", "Vacía"
    UNCERTAIN = "uncertain", "Dudosa"


class CalvingOutcome(models.TextChoices):
    LIVE = "live", "Vivo"
    STILLBORN = "stillborn", "Muerto al nacer"
    ABORTED = "aborted", "Aborto"


class CalvingEase(models.TextChoices):
    NORMAL = "normal", "Normal"
    ASSISTED = "assisted", "Asistido"
    CAESAREAN = "caesarean", "Cesárea"


class WeaningPurpose(models.TextChoices):
    REPLACEMENT = "replacement", "Reposición"
    SALE = "sale", "Venta"
    UNDECIDED = "undecided", "Sin definir"


class IatfProtocol(models.Model):
    """A reusable IATF protocol template — editable master data (decision 5)."""

    name = models.CharField(max_length=200)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class IatfProtocolStep(models.Model):
    """One step at a relative `day_offset`. Absolute dates DERIVE from the
    Service date, never stored in the template (decision 5)."""

    protocol = models.ForeignKey(
        IatfProtocol, on_delete=models.CASCADE, related_name="steps"
    )
    day_offset = models.IntegerField()
    action = models.CharField(max_length=200)
    product = models.CharField(max_length=200, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["protocol", "day_offset", "id"]

    def __str__(self):
        return f"{self.protocol_id} d{self.day_offset} {self.action}"


class Service(LifecycleEvent):
    """An insemination/service event. Only ai/iatf on a boarding client posts a
    `service` debit for the insemination fee (decision 6); natural/own/embryo post
    none. Decrements a genetics semen/embryo movement `out` (decision 7)."""

    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="breeding_services"
    )
    method = models.CharField(max_length=16, choices=Method.choices)
    sire = models.ForeignKey(
        "genetics.Sire", on_delete=models.PROTECT, null=True, blank=True,
        related_name="services",
    )
    semen_batch = models.ForeignKey(
        "genetics.SemenBatch", on_delete=models.PROTECT, null=True, blank=True,
        related_name="services",
    )
    embryo_batch = models.ForeignKey(
        "genetics.EmbryoBatch", on_delete=models.PROTECT, null=True, blank=True,
        related_name="services",
    )
    protocol = models.ForeignKey(
        IatfProtocol, on_delete=models.PROTECT, null=True, blank=True,
        related_name="services",
    )
    # Snapshotted as the insemination fee when it posts a debit (adr-25 regla 3).
    service_price = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta(LifecycleEvent.Meta):
        abstract = False
        constraints = [
            models.CheckConstraint(
                name="service_target_animal_xor_lot",
                condition=(
                    models.Q(animal__isnull=False, lot__isnull=True)
                    | models.Q(animal__isnull=True, lot__isnull=False)
                ),
            )
        ]

    def __str__(self):
        return f"Service {self.date} {self.method}"


class PregnancyCheck(LifecycleEvent):
    """A pregnancy diagnosis (tacto). Posts no ledger entry. The estimated calving
    date is DERIVED, never stored (decision 3)."""

    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="pregnancy_checks"
    )
    method = models.CharField(max_length=12, choices=PregnancyMethod.choices)
    result = models.CharField(max_length=10, choices=PregnancyResult.choices)
    gestation_days = models.PositiveIntegerField(null=True, blank=True)
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, null=True, blank=True,
        related_name="pregnancy_checks",
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta(LifecycleEvent.Meta):
        abstract = False
        constraints = [
            models.CheckConstraint(
                name="pregnancycheck_target_animal_xor_lot",
                condition=(
                    models.Q(animal__isnull=False, lot__isnull=True)
                    | models.Q(animal__isnull=True, lot__isnull=False)
                ),
            )
        ]

    @property
    def estimated_calving_date(self):
        """Derived: check date + remaining gestation. Never stored (decision 3)."""
        if self.result != PregnancyResult.PREGNANT or self.gestation_days is None:
            return None
        return self.date + timedelta(days=GESTATION_DAYS - self.gestation_days)

    def __str__(self):
        return f"PregnancyCheck {self.date} {self.result}"


class Calving(LifecycleEvent):
    """A calving (parición). A live individual calving creates the calf Animal
    (decision 4); genealogy is DERIVED (dam=target, sire=service.sire). No ledger."""

    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="calvings"
    )
    outcome = models.CharField(max_length=10, choices=CalvingOutcome.choices)
    calving_ease = models.CharField(
        max_length=10, choices=CalvingEase.choices, default=CalvingEase.NORMAL
    )
    calf_sex = models.CharField(max_length=6, blank=True)
    calf_weight = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    births_count = models.PositiveIntegerField(null=True, blank=True)
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, null=True, blank=True,
        related_name="calvings",
    )
    calf = models.ForeignKey(
        "livestock.Animal", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="birth_calving",
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta(LifecycleEvent.Meta):
        abstract = False
        constraints = [
            models.CheckConstraint(
                name="calving_target_animal_xor_lot",
                condition=(
                    models.Q(animal__isnull=False, lot__isnull=True)
                    | models.Q(animal__isnull=True, lot__isnull=False)
                ),
            )
        ]

    def __str__(self):
        return f"Calving {self.date} {self.outcome}"


class Weaning(LifecycleEvent):
    """A weaning (destete). Records weaning weight and the calf's purpose. No ledger."""

    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="weanings"
    )
    weaning_weight = models.DecimalField(max_digits=8, decimal_places=2)
    purpose = models.CharField(
        max_length=12, choices=WeaningPurpose.choices, default=WeaningPurpose.UNDECIDED
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta(LifecycleEvent.Meta):
        abstract = False
        constraints = [
            models.CheckConstraint(
                name="weaning_target_animal_xor_lot",
                condition=(
                    models.Q(animal__isnull=False, lot__isnull=True)
                    | models.Q(animal__isnull=True, lot__isnull=False)
                ),
            )
        ]

    def __str__(self):
        return f"Weaning {self.date} {self.weaning_weight}"
