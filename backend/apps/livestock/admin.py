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


from apps.livestock.models import Death, Exit, Weighing


@admin.register(Weighing)
class WeighingAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "animal", "lot", "weight", "head_count", "method")
    list_filter = ("date", "method")


@admin.register(Death)
class DeathAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "animal", "lot", "cause", "head_count")
    list_filter = ("date", "cause")


@admin.register(Exit)
class ExitAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "animal", "lot", "kind", "head_count", "destination")
    list_filter = ("date", "kind")
