from django.contrib import admin

from apps.feedyard.models import BunkScore, LoadingOrder, Pen, Ration, RationLine


class RationLineInline(admin.TabularInline):
    model = RationLine
    extra = 1


@admin.register(Pen)
class PenAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "capacity_head", "status")
    list_filter = ("status",)
    search_fields = ("code", "name")


@admin.register(Ration)
class RationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    inlines = [RationLineInline]


@admin.register(LoadingOrder)
class LoadingOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "pen", "ration", "planned_as_fed_kg")
    list_filter = ("date", "pen")
    readonly_fields = ("created_at",)


@admin.register(BunkScore)
class BunkScoreAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "pen", "score")
    list_filter = ("date", "pen", "score")
    readonly_fields = ("created_at",)
