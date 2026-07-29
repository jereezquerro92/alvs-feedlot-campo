"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

"""Extra expenses: the field manager's "carga de deudas" as chargeable events.

`ExpenseEvent` is a `CostedEvent` ([[adr-32-multi-rubro-assets]] decision 1): it
snapshots `unit_price`×`quantity` and (via `register_expense`) posts a `service`
`debit` through the ledger's generic `(source_kind, source_id)` seam
([[adr-24-feedlot-domain]] rule 4) — the in-doctrine rendering of
[[adr-44-field-operational-roles]] decision 6 ("carga de deudas" via events, never
a manual ledger debit). An optional `lot` attributes the charge to one lot of the
client (null = the whole client). English `choices`; Spanish only in rendered output.
"""

from django.db import models

from apps.assets.models import CostedEvent


class ExpenseEvent(CostedEvent):
    """A billed extra expense (labor / fuel / machinery / other). Immutable event
    that posts a `service` debit (adr-44 decision 6). `quantity`×`unit_price` reads
    as horas×precio/hora (labor), litros×precio/litro (fuel), or cantidad×precio."""

    class Category(models.TextChoices):
        LABOR = "labor", "Mano de obra"
        FUEL = "fuel", "Combustible"
        MACHINERY = "machinery", "Maquinaria"
        OTHER = "other", "Otro"

    title = models.CharField(max_length=120)
    category = models.CharField(
        max_length=12, choices=Category.choices, default=Category.OTHER
    )
    # Optional attribution to one lot of the client; null = the whole client ("todos").
    lot = models.ForeignKey(
        "livestock.Lot", on_delete=models.PROTECT, null=True, blank=True,
        related_name="+",
    )
    # Free label for the fuel type (diesel, nafta, …); blank for non-fuel expenses.
    fuel_kind = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["client", "date"]),
            models.Index(fields=["category", "date"]),
        ]

    def __str__(self):
        return f"ExpenseEvent {self.date} {self.title}"
