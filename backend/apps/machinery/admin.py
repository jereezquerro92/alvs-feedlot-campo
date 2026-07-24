from django.contrib import admin

from apps.machinery.models import Machine, MaintenanceEvent


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "client", "category", "status")
    list_filter = ("category", "status")
    search_fields = ("name", "code")


@admin.register(MaintenanceEvent)
class MaintenanceEventAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "client", "machine", "title", "kind", "total_cost")
    list_filter = ("date", "kind")
    readonly_fields = ("created_at",)
