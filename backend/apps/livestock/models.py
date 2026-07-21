"""Cattle: animals, lots and intake (docs/adrs/adr-26-livestock-individual-and-lot.md).

Cattle enter individually (one Animal per ear tag) or as a lot (head count +
total weight, no per-head identity). Both modes are first-class. Lot counters
are maintained by events, never hand-edited.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models


class Category(models.TextChoices):
    COW = "cow", "Vaca"
    BULL = "bull", "Toro"
    STEER = "steer", "Novillo"
    HEIFER = "heifer", "Vaquillona"
    CALF = "calf", "Ternero/a"


class Sex(models.TextChoices):
    MALE = "male", "Macho"
    FEMALE = "female", "Hembra"


class Lot(models.Model):
    class Mode(models.TextChoices):
        ANONYMOUS = "anonymous", "Anónimo (cabezas + kg)"
        NAMED = "named", "Nominado (agrupa animales)"

    class Status(models.TextChoices):
        ACTIVE = "active", "Activo"
        CLOSED = "closed", "Cerrado"

    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="lots")
    code = models.CharField(max_length=40)
    mode = models.CharField(max_length=12, choices=Mode.choices, default=Mode.ANONYMOUS)
    head_count = models.PositiveIntegerField(default=0)
    total_weight = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["client", "code"]

    def __str__(self):
        return f"{self.code} ({self.client_id})"


class Animal(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Activo"
        DEAD = "dead", "Muerto"
        SOLD = "sold", "Vendido"
        EXITED = "exited", "Egresado"

    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="animals")
    lot = models.ForeignKey(
        Lot, on_delete=models.SET_NULL, null=True, blank=True, related_name="animals"
    )
    ear_tag = models.CharField(max_length=40)
    category = models.CharField(max_length=8, choices=Category.choices)
    sex = models.CharField(max_length=6, choices=Sex.choices, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.ACTIVE)
    entry_date = models.DateField()
    entry_weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    current_weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["client", "ear_tag"]
        constraints = [
            models.UniqueConstraint(
                fields=["client", "ear_tag"],
                condition=models.Q(status="active"),
                name="unique_active_ear_tag_per_client",
            )
        ]

    def __str__(self):
        return self.ear_tag


class Intake(models.Model):
    class Mode(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        LOT = "lot", "Lote"

    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="intakes")
    date = models.DateField()
    mode = models.CharField(max_length=12, choices=Mode.choices)
    head_count = models.PositiveIntegerField(null=True, blank=True)
    total_weight = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    lot = models.ForeignKey(Lot, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"Intake {self.date} ({self.mode})"


class LifecycleEvent(models.Model):
    """Shared shape for events that target one Animal XOR one Lot (adr-26 rule 3).

    Abstract on purpose: Weighing, Death and Exit each own their table, but the
    target pair and its constraint are identical and must not drift apart.
    """

    animal = models.ForeignKey(
        Animal, on_delete=models.PROTECT, null=True, blank=True, related_name="%(class)ss"
    )
    lot = models.ForeignKey(
        Lot, on_delete=models.PROTECT, null=True, blank=True, related_name="%(class)ss"
    )
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        abstract = True
        ordering = ["-date", "-id"]

    @property
    def target(self):
        return self.animal or self.lot


class Weighing(LifecycleEvent):
    """A weight reading. For lots, `weight` is the TOTAL kg of `head_count` head."""

    class Method(models.TextChoices):
        SCALE = "scale", "Báscula"
        ESTIMATED = "estimated", "Estimado"

    weight = models.DecimalField(max_digits=12, decimal_places=2)
    head_count = models.PositiveIntegerField(null=True, blank=True)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.SCALE)
    notes = models.CharField(max_length=255, blank=True)

    class Meta(LifecycleEvent.Meta):
        abstract = False
        ordering = ["date", "id"]
        constraints = [
            models.CheckConstraint(
                name="weighing_target_animal_xor_lot",
                condition=(
                    models.Q(animal__isnull=False, lot__isnull=True)
                    | models.Q(animal__isnull=True, lot__isnull=False)
                ),
            )
        ]

    @property
    def weight_per_head(self):
        """Lot readings are only comparable per head (see docs/feedlot/11-plan-de-fases.md)."""
        if self.lot_id and self.head_count:
            return self.weight / Decimal(self.head_count)
        return self.weight

    def __str__(self):
        return f"Weighing {self.date} {self.weight}"


class Death(LifecycleEvent):
    """A death. Never touches the ledger: feed already consumed stays billed."""

    class Cause(models.TextChoices):
        DISEASE = "disease", "Enfermedad"
        ACCIDENT = "accident", "Accidente"
        UNKNOWN = "unknown", "Desconocida"
        OTHER = "other", "Otra"

    cause = models.CharField(max_length=10, choices=Cause.choices, default=Cause.UNKNOWN)
    cause_detail = models.CharField(max_length=255, blank=True)
    head_count = models.PositiveIntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta(LifecycleEvent.Meta):
        abstract = False
        constraints = [
            models.CheckConstraint(
                name="death_target_animal_xor_lot",
                condition=(
                    models.Q(animal__isnull=False, lot__isnull=True)
                    | models.Q(animal__isnull=True, lot__isnull=False)
                ),
            )
        ]

    def __str__(self):
        return f"Death {self.date} ({self.cause})"


class Exit(LifecycleEvent):
    """An exit: sale, transfer back to the client, or other. Informational price only."""

    class Kind(models.TextChoices):
        SALE = "sale", "Venta"
        TRANSFER = "transfer", "Retiro"
        OTHER = "other", "Otro"

    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.SALE)
    destination = models.CharField(max_length=120, blank=True)
    head_count = models.PositiveIntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sale_price_per_kg = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )

    class Meta(LifecycleEvent.Meta):
        abstract = False
        constraints = [
            models.CheckConstraint(
                name="exit_target_animal_xor_lot",
                condition=(
                    models.Q(animal__isnull=False, lot__isnull=True)
                    | models.Q(animal__isnull=True, lot__isnull=False)
                ),
            )
        ]

    def __str__(self):
        return f"Exit {self.date} ({self.kind})"
