"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

"""Genetics: sires, semen/embryo inventory and semen sales (adr-47).

Catalogs (Sire, BreedingValue, SemenBatch, EmbryoBatch) are editable master
data; movements, flushes and sales are immutable dated events. Straw and embryo
stock is DERIVED Σin − Σout of the movements, never a stored field (decision 2).
Only a SemenSale posts a ledger entry — a `sale` credit to the own account
(decision 4); every other event posts none (decision 6).
"""

from django.conf import settings
from django.db import models


class Trait(models.TextChoices):
    BIRTH_WEIGHT = "birth_weight", "Peso al nacer"
    WEANING_WEIGHT = "weaning_weight", "Peso al destete"
    MILK = "milk", "Leche"
    RIBEYE_AREA = "ribeye_area", "Área de ojo de bife"
    MARBLING = "marbling", "Marmoleo"
    SCROTAL = "scrotal", "Circunferencia escrotal"
    OTHER = "other", "Otro"


class Direction(models.TextChoices):
    IN = "in", "Entrada"
    OUT = "out", "Salida"


class SemenReason(models.TextChoices):
    PURCHASE = "purchase", "Compra"
    COLLECTION = "collection", "Colecta"
    INSEMINATION = "insemination", "Inseminación"
    SALE = "sale", "Venta"
    DISCARD = "discard", "Descarte"
    ADJUSTMENT = "adjustment", "Ajuste"


class EmbryoReason(models.TextChoices):
    COLLECTION = "collection", "Colecta"
    TRANSFER = "transfer", "Transferencia"
    SALE = "sale", "Venta"
    DISCARD = "discard", "Descarte"
    ADJUSTMENT = "adjustment", "Ajuste"


class Sire(models.Model):
    """A breeding bull — own (links an Animal) or external (registry_id/breed)."""

    name = models.CharField(max_length=200)
    breed = models.CharField(max_length=120, blank=True)
    animal = models.ForeignKey(
        "livestock.Animal",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sire_records",
    )
    registry_id = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class BreedingValue(models.Model):
    """A DEP/EPD row — loaded from an external genetic evaluation (decision 3)."""

    sire = models.ForeignKey(Sire, on_delete=models.PROTECT, related_name="breeding_values")
    trait = models.CharField(max_length=20, choices=Trait.choices)
    value = models.DecimalField(max_digits=12, decimal_places=4)
    accuracy = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    source = models.CharField(max_length=120, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sire", "trait", "-date"]

    def __str__(self):
        return f"{self.sire_id} {self.trait}={self.value}"


class SemenBatch(models.Model):
    """A straw batch. Straws remaining = Σin − Σout of its movements (decision 2)."""

    sire = models.ForeignKey(Sire, on_delete=models.PROTECT, related_name="semen_batches")
    batch_code = models.CharField(max_length=80)
    collection_date = models.DateField(null=True, blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    tank = models.CharField(max_length=80, blank=True)
    position = models.CharField(max_length=80, blank=True)
    # Informational — values the stock, never posts a charge (decision 6).
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sire", "batch_code"]

    def __str__(self):
        return self.batch_code


class SemenMovement(models.Model):
    """An immutable in/out straw movement. Posts no ledger entry (decision 6)."""

    semen_batch = models.ForeignKey(
        SemenBatch, on_delete=models.PROTECT, related_name="movements"
    )
    direction = models.CharField(max_length=3, choices=Direction.choices)
    straws = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=16, choices=SemenReason.choices)
    date = models.DateField()
    source_kind = models.CharField(max_length=40, blank=True)
    source_id = models.PositiveIntegerField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["semen_batch", "date"])]

    def __str__(self):
        return f"SemenMovement {self.direction} {self.straws} ({self.semen_batch_id})"


class SemenSale(models.Model):
    """An immutable semen sale. Posts a `sale` credit to the own account (decision 4)."""

    semen_batch = models.ForeignKey(
        SemenBatch, on_delete=models.PROTECT, related_name="sales"
    )
    date = models.DateField()
    straws = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=14, decimal_places=4)
    buyer_name = models.CharField(max_length=200, blank=True)
    buyer_client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="semen_purchases",
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]

    @property
    def total_price(self):
        return self.straws * self.unit_price

    def __str__(self):
        return f"SemenSale {self.date} {self.straws}×{self.unit_price}"


class EmbryoBatch(models.Model):
    """An embryo batch. Embryos remaining = Σin − Σout of its movements (decision 2)."""

    donor = models.ForeignKey(
        "livestock.Animal", on_delete=models.PROTECT, related_name="embryo_batches"
    )
    sire = models.ForeignKey(
        Sire, on_delete=models.PROTECT, null=True, blank=True, related_name="embryo_batches"
    )
    grade = models.CharField(max_length=40, blank=True)
    flush_date = models.DateField(null=True, blank=True)
    tank = models.CharField(max_length=80, blank=True)
    position = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["donor", "-flush_date"]

    def __str__(self):
        return f"EmbryoBatch<{self.donor_id}> {self.grade}"


class EmbryoMovement(models.Model):
    """An immutable in/out embryo movement. Posts no ledger entry (decision 6)."""

    embryo_batch = models.ForeignKey(
        EmbryoBatch, on_delete=models.PROTECT, related_name="movements"
    )
    direction = models.CharField(max_length=3, choices=Direction.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=16, choices=EmbryoReason.choices)
    date = models.DateField()
    source_kind = models.CharField(max_length=40, blank=True)
    source_id = models.PositiveIntegerField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["embryo_batch", "date"])]

    def __str__(self):
        return f"EmbryoMovement {self.direction} {self.quantity} ({self.embryo_batch_id})"


class EmbryoFlush(models.Model):
    """A donor collection (colecta). Produces inventory: creates/updates an
    EmbryoBatch and posts an EmbryoMovement `in` (decision 5). Posts no ledger."""

    donor = models.ForeignKey(
        "livestock.Animal", on_delete=models.PROTECT, related_name="embryo_flushes"
    )
    sire = models.ForeignKey(
        Sire, on_delete=models.PROTECT, null=True, blank=True, related_name="embryo_flushes"
    )
    date = models.DateField()
    embryos_collected = models.DecimalField(max_digits=12, decimal_places=2)
    grade = models.CharField(max_length=40, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"EmbryoFlush {self.date} <{self.donor_id}> {self.embryos_collected}"
