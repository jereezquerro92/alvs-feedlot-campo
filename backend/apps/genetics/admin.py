"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

from django.contrib import admin

from apps.genetics.models import (
    BreedingValue,
    EmbryoBatch,
    EmbryoFlush,
    EmbryoMovement,
    SemenBatch,
    SemenMovement,
    SemenSale,
    Sire,
)


@admin.register(Sire)
class SireAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "breed", "animal", "registry_id", "is_active")
    list_filter = ("is_active", "breed")
    search_fields = ("name", "registry_id")


@admin.register(BreedingValue)
class BreedingValueAdmin(admin.ModelAdmin):
    list_display = ("id", "sire", "trait", "value", "accuracy", "date")
    list_filter = ("trait",)
    search_fields = ("source",)


@admin.register(SemenBatch)
class SemenBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "batch_code", "sire", "supplier", "tank", "is_active")
    list_filter = ("is_active",)
    search_fields = ("batch_code", "supplier")


@admin.register(EmbryoBatch)
class EmbryoBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "donor", "sire", "grade", "flush_date", "is_active")
    list_filter = ("is_active", "grade")


@admin.register(SemenMovement)
class SemenMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "semen_batch", "direction", "straws", "reason", "date")
    list_filter = ("direction", "reason")
    readonly_fields = tuple(f.name for f in SemenMovement._meta.fields)


@admin.register(SemenSale)
class SemenSaleAdmin(admin.ModelAdmin):
    list_display = ("id", "semen_batch", "straws", "unit_price", "buyer_name", "date")
    search_fields = ("buyer_name",)
    readonly_fields = tuple(f.name for f in SemenSale._meta.fields)


@admin.register(EmbryoMovement)
class EmbryoMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "embryo_batch", "direction", "quantity", "reason", "date")
    list_filter = ("direction", "reason")
    readonly_fields = tuple(f.name for f in EmbryoMovement._meta.fields)


@admin.register(EmbryoFlush)
class EmbryoFlushAdmin(admin.ModelAdmin):
    list_display = ("id", "donor", "sire", "embryos_collected", "grade", "date")
    readonly_fields = tuple(f.name for f in EmbryoFlush._meta.fields)
