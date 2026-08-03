"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

"""SENASA traceability (adr-38): RENSPA, DT-e and caravana.

Establishment is an editable RENSPA catalog; TransitDocument (the DT-e) and Caravana
are immutable events. Nothing here posts a ledger entry (decision 2) — traceability is
documental, not economic. The caravana references the existing Animal without touching
`livestock` (decision 4, adr-32 rule 2 forward-only extraction).
"""

from django.conf import settings
from django.db import models


class Establishment(models.Model):
    """An editable establishment registered in SENASA by its RENSPA."""

    renspa = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=160)
    holder = models.CharField(max_length=160, blank=True)
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.renspa})"


class TransitDocument(models.Model):
    """A DT-e: an immutable transit that links an origin RENSPA to a destination RENSPA.

    Posts no ledger entry (decision 2). Categories mirror livestock categories but are
    kept local — a transit is a documental fact, not a herd mutation.
    """

    class Category(models.TextChoices):
        COW = "cow", "Vaca"
        BULL = "bull", "Toro"
        STEER = "steer", "Novillo"
        HEIFER = "heifer", "Vaquillona"
        CALF = "calf", "Ternero/a"
        MIXED = "mixed", "Mixto"

    dte_number = models.CharField(max_length=40, unique=True)
    origin = models.ForeignKey(
        Establishment, on_delete=models.PROTECT, related_name="transits_out"
    )
    destination = models.ForeignKey(
        Establishment, on_delete=models.PROTECT, related_name="transits_in"
    )
    date = models.DateField()
    category = models.CharField(max_length=8, choices=Category.choices, default=Category.MIXED)
    head_count = models.PositiveIntegerField()
    total_weight = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    lot = models.ForeignKey(
        "livestock.Lot", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="transits",
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["origin", "destination", "-date"])]

    def __str__(self):
        return f"DT-e {self.dte_number}"


class Caravana(models.Model):
    """The official individual caravan number bound to an Animal. Immutable, unique."""

    official_number = models.CharField(max_length=40, unique=True)
    animal = models.ForeignKey(
        "livestock.Animal", on_delete=models.PROTECT, related_name="caravanas"
    )
    assigned_date = models.DateField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-assigned_date", "-id"]
        indexes = [models.Index(fields=["animal"])]

    def __str__(self):
        return self.official_number
