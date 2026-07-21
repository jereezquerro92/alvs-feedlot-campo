from django.contrib import admin

from apps.sanitary.models import HealthEvent, HealthProduct


@admin.register(HealthProduct)
class HealthProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "kind", "unit", "unit_price", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("name",)


@admin.register(HealthEvent)
class HealthEventAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "client", "product", "quantity", "unit_price", "total_cost")
    list_filter = ("date", "product")
    readonly_fields = ("created_at",)
