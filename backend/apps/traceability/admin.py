"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

from django.contrib import admin

from apps.traceability.models import Caravana, Establishment, TransitDocument


@admin.register(Establishment)
class EstablishmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "renspa", "holder", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "renspa", "holder")


@admin.register(TransitDocument)
class TransitDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "dte_number", "origin", "destination", "category", "head_count", "date")
    list_filter = ("category",)
    search_fields = ("dte_number",)
    readonly_fields = tuple(f.name for f in TransitDocument._meta.fields)


@admin.register(Caravana)
class CaravanaAdmin(admin.ModelAdmin):
    list_display = ("id", "official_number", "animal", "assigned_date")
    search_fields = ("official_number",)
    readonly_fields = tuple(f.name for f in Caravana._meta.fields)
