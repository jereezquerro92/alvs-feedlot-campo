from django.contrib import admin

from apps.livestock.models import Animal, Intake, Lot


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "client", "mode", "head_count", "total_weight", "status")
    list_filter = ("mode", "status")
    search_fields = ("code",)


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ("id", "ear_tag", "client", "lot", "category", "status", "current_weight")
    list_filter = ("category", "status")
    search_fields = ("ear_tag",)


@admin.register(Intake)
class IntakeAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "date", "mode", "head_count", "total_weight")
    list_filter = ("mode",)
