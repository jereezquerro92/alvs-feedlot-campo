"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

from django.contrib import admin

from apps.breeding.models import (
    Calving,
    IatfProtocol,
    IatfProtocolStep,
    PregnancyCheck,
    Service,
    Weaning,
)


class IatfProtocolStepInline(admin.TabularInline):
    model = IatfProtocolStep
    extra = 0


@admin.register(IatfProtocol)
class IatfProtocolAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    inlines = [IatfProtocolStepInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("date", "method", "client", "animal", "lot", "sire", "service_price")
    list_filter = ("method",)
    date_hierarchy = "date"


@admin.register(PregnancyCheck)
class PregnancyCheckAdmin(admin.ModelAdmin):
    list_display = ("date", "result", "method", "client", "animal", "lot")
    list_filter = ("result", "method")
    date_hierarchy = "date"


@admin.register(Calving)
class CalvingAdmin(admin.ModelAdmin):
    list_display = ("date", "outcome", "calving_ease", "client", "animal", "lot", "calf")
    list_filter = ("outcome", "calving_ease")
    date_hierarchy = "date"


@admin.register(Weaning)
class WeaningAdmin(admin.ModelAdmin):
    list_display = ("date", "client", "animal", "lot", "weaning_weight", "purpose")
    list_filter = ("purpose",)
    date_hierarchy = "date"
