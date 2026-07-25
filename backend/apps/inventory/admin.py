"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

from django.contrib import admin

from apps.inventory.models import InputStockMovement, InputType


@admin.register(InputType)
class InputTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "unit", "category", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("name",)


@admin.register(InputStockMovement)
class InputStockMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "input_type", "direction", "quantity", "owner_kind", "client", "date")
    list_filter = ("direction", "owner_kind")
    search_fields = ("note",)
    readonly_fields = tuple(f.name for f in InputStockMovement._meta.fields)
