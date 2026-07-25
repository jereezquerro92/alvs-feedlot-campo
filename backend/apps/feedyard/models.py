"""Feedyard: the daily pen operating loop (adr-33-feedyard-operating-loop).

This app is planning and monitoring — it NEVER posts a ledger entry (decision 1).
Billing stays exclusively in `feed` (adr-25 rule 4). `Pen`/`Ration`/`RationLine`
are editable catalogs; `LoadingOrder` (the planned mixer load) and `BunkScore`
(the daily feed-trough reading) are immutable events (decision 5). The executed,
charged ration is still `feed.FeedingEvent`, which gains an optional `pen`
grouping (decisions 2, 3). English choices; Spanish only in rendered output.
"""

from django.conf import settings
from django.db import models


class Pen(models.Model):
    """A physical corral. Editable catalog (adr-33 decision 5)."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Activo"
        INACTIVE = "inactive", "Inactivo"

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120, blank=True)
    capacity_head = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.ACTIVE
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class Ration(models.Model):
    """A named diet/recipe. Composition lives in `RationLine`; no price of its own
    (adr-33 decision 4). Editable catalog."""

    name = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RationLine(models.Model):
    """One share of a `Ration`: which feed, in what as-fed proportion, at what dry
    matter. Edited nested under its ration (adr-33 decision 4)."""

    ration = models.ForeignKey(Ration, on_delete=models.CASCADE, related_name="lines")
    feed_type = models.ForeignKey("feed.FeedType", on_delete=models.PROTECT)
    proportion = models.DecimalField(
        max_digits=6, decimal_places=3, help_text="Percent, as-fed."
    )
    dry_matter_pct = models.DecimalField(max_digits=6, decimal_places=3)

    class Meta:
        ordering = ["ration", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["ration", "feed_type"], name="rationline_unique_feed_per_ration"
            )
        ]

    def __str__(self):
        return f"{self.feed_type_id} @ {self.proportion}% of ration {self.ration_id}"


class LoadingOrder(models.Model):
    """The PLANNED mixer load for a pen and a ration (orden de carga). Immutable;
    posts NO ledger entry (adr-33 decisions 1, 2). The executed ration is
    `feed.FeedingEvent`, and the plan-vs-real gap is the management datum."""

    pen = models.ForeignKey(Pen, on_delete=models.PROTECT, related_name="loading_orders")
    ration = models.ForeignKey(
        Ration, on_delete=models.PROTECT, related_name="loading_orders"
    )
    date = models.DateField()
    planned_as_fed_kg = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["pen", "date"])]

    def __str__(self):
        return f"LoadingOrder {self.date} pen={self.pen_id} {self.planned_as_fed_kg}kg"


class PenPlacement(models.Model):
    """An immutable event moving an Animal or Lot into/out of a Pen (adr-34).

    Pen occupancy is DERIVED from these events (decision 1); it is never a stored
    field. Exactly one of animal/lot is set (decision 2, XOR CHECK). Posts NO
    ledger entry (decision 3)."""

    class Direction(models.TextChoices):
        IN = "in", "Ingreso a corral"
        OUT = "out", "Egreso de corral"

    pen = models.ForeignKey(Pen, on_delete=models.PROTECT, related_name="placements")
    animal = models.ForeignKey(
        "livestock.Animal", on_delete=models.PROTECT, null=True, blank=True,
        related_name="pen_placements",
    )
    lot = models.ForeignKey(
        "livestock.Lot", on_delete=models.PROTECT, null=True, blank=True,
        related_name="pen_placements",
    )
    date = models.DateField()
    direction = models.CharField(max_length=3, choices=Direction.choices)
    head_count = models.PositiveIntegerField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["pen", "date"]),
            models.Index(fields=["animal", "date"]),
            models.Index(fields=["lot", "date"]),
        ]
        constraints = [
            # An animal XOR a lot — exactly one target (adr-26 rule 3, adr-34 decision 2).
            models.CheckConstraint(
                name="penplacement_target_animal_xor_lot",
                condition=(
                    models.Q(animal__isnull=False, lot__isnull=True)
                    | models.Q(animal__isnull=True, lot__isnull=False)
                ),
            )
        ]

    @property
    def head(self):
        """Head moved by this event: `head_count` for a lot, 1 for an animal."""
        return self.head_count if self.lot_id else 1

    def __str__(self):
        return f"PenPlacement {self.date} {self.direction} pen={self.pen_id}"


class BunkScore(models.Model):
    """A daily bunk (feed-trough) reading for a pen (adr-33). Score 0–4 is the
    industry bunk-reading scale. Immutable; posts NO ledger entry."""

    pen = models.ForeignKey(Pen, on_delete=models.PROTECT, related_name="bunk_scores")
    date = models.DateField()
    score = models.PositiveSmallIntegerField(help_text="Bunk-reading scale 0–4.")
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["pen", "date"])]
        constraints = [
            models.CheckConstraint(
                name="bunkscore_score_0_to_4",
                condition=models.Q(score__gte=0, score__lte=4),
            )
        ]

    def __str__(self):
        return f"BunkScore {self.date} pen={self.pen_id} score={self.score}"
