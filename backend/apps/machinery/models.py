"""Machinery rubro: machines and their maintenance (adr-32-multi-rubro-assets).

`Machine` is a concrete `AssetBase`. `MaintenanceEvent` is a chargeable
`CostedEvent` that posts a `service` debit through the ledger's generic seam
(adr-32 decisions 3, 5) — same seam the crops rubro uses, `ledger` unchanged.
Maintenance stock/parts inventory is deliberately out of scope for this phase
(add when a need proves real). English choices; Spanish only in rendered output.
"""

from django.db import models

from apps.assets.models import AssetBase, CostedEvent


class Machine(AssetBase):
    """A piece of machinery (maquinaria). Editable catalog (adr-32 decision 6)."""

    class Category(models.TextChoices):
        TRACTOR = "tractor", "Tractor"
        HARVESTER = "harvester", "Cosechadora"
        MIXER = "mixer", "Mixer"
        TRUCK = "truck", "Camión"
        OTHER = "other", "Otro"

    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="machines"
    )
    category = models.CharField(
        max_length=12, choices=Category.choices, default=Category.OTHER
    )

    class Meta:
        ordering = ["client", "name"]


class MaintenanceEvent(CostedEvent):
    """A service/repair on a machine (mantenimiento). Posts a `service` debit."""

    class Kind(models.TextChoices):
        PREVENTIVE = "preventive", "Preventivo"
        CORRECTIVE = "corrective", "Correctivo"
        OTHER = "other", "Otro"

    machine = models.ForeignKey(
        Machine, on_delete=models.PROTECT, related_name="maintenance_events"
    )
    kind = models.CharField(
        max_length=12, choices=Kind.choices, default=Kind.PREVENTIVE
    )
    title = models.CharField(max_length=120)
    hours = models.DecimalField(
        max_digits=10, decimal_places=1, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["client", "date"]),
            models.Index(fields=["machine", "date"]),
        ]

    def __str__(self):
        return f"Maintenance {self.date} {self.title}"
