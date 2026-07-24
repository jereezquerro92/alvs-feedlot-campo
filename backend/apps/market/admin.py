from django.contrib import admin

from apps.market.models import MarketPrice, MarketSource


@admin.register(MarketSource)
class MarketSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "kind", "is_active", "is_automated")
    list_filter = ("kind", "is_active", "is_automated")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    """The manual-load surface: add a MarketPrice here when a source is down."""

    list_display = ("date", "source", "category", "price_avg", "price_min", "price_max", "head_count")
    list_filter = ("source", "date", "category")
    search_fields = ("category",)
    date_hierarchy = "date"
