"""Cattle: animals, lots and intake (docs/adrs/adr-26-livestock-individual-and-lot.md).

Cattle enter individually (one Animal per ear tag) or as a lot (head count +
total weight, no per-head identity). Both modes are first-class. Lot counters
are maintained by events, never hand-edited.
"""

from decimal import Decimal

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
