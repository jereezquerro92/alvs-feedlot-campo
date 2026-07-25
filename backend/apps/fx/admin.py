from django.contrib import admin

from apps.fx.models import FxRate


@admin.register(FxRate)
class FxRateAdmin(admin.ModelAdmin):
    list_display = ("id", "currency", "date", "rate", "source")
    list_filter = ("currency", "source")
    search_fields = ("currency",)
