from django.contrib import admin

from apps.crops.models import Crop, Cutting, FieldTask, Pivot


@admin.register(Pivot)
class PivotAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "client", "area_ha", "status")
    list_filter = ("status",)
    search_fields = ("name", "code")


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ("id", "pivot", "species", "sown_date", "status")
    list_filter = ("species", "status")


@admin.register(Cutting)
class CuttingAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "crop", "kg_harvested", "bales", "quality")
    list_filter = ("date", "quality")
    readonly_fields = ("created_at",)


@admin.register(FieldTask)
class FieldTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "client", "pivot", "title", "category", "total_cost")
    list_filter = ("date", "category")
    readonly_fields = ("created_at",)
