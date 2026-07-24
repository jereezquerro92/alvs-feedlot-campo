"""Shared abstractions for asset-bearing rubros (adr-32-multi-rubro-assets).

`assets` contributes NO concrete tables: it exposes two abstract bases that the
`crops` and `machinery` apps inherit. Same idiom as livestock's `LifecycleEvent`
(adr-28 decision 1) — share the shape, not the domain. Extracted only now, with
the first second rubro (crops + machinery); it was rightly absent when a single
rubro existed (docs/feedlot/14-preparacion-fase6.md, YAGNI).
"""

from decimal import Decimal

from django.conf import settings
from django.db import models


class AssetBase(models.Model):
    """Lifecycle base for a concrete asset (a `Pivot`, a `Machine`).

    A retired asset (`status=retired`) is rejected by the domain services, not by
    the view — the same posture a dead animal has (adr-28).
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Activo"
        RETIRED = "retired", "Dado de baja"

    name = models.CharField(max_length=120)
    code = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.ACTIVE)
    acquired_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class CostedEvent(models.Model):
    """Base for a chargeable event: snapshots `unit_price`×`quantity` and (via its
    domain service) posts a `service` debit through the generic `(source_kind,
    source_id)` seam (adr-32 decision 3). `client` is mandatory — the feedlot's own
    costs ride its own `Client(kind=own)` account (adr-32 decision 5).

    The reverse accessors are disabled (`related_name="+"`) because two concrete
    subclasses inherit the same FKs; queries filter on `client_id` directly.
    """

    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="+"
    )
    date = models.DateField()
    unit_price = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0"))
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("1"))
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
    )

    class Meta:
        abstract = True

    @property
    def total_cost(self):
        return (self.quantity or Decimal("0")) * (self.unit_price or Decimal("0"))
