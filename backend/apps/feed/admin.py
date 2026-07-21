from django.contrib import admin

from apps.feed.models import FeedDelivery, FeedingEvent, FeedStockMovement, FeedType


@admin.register(FeedType)
class FeedTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "unit", "category", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(FeedDelivery)
class FeedDeliveryAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "feed_type", "quantity", "date")
    list_filter = ("feed_type",)


@admin.register(FeedStockMovement)
class FeedStockMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "owner_kind", "client", "feed_type", "direction", "quantity", "date")
    list_filter = ("owner_kind", "direction", "feed_type")


@admin.register(FeedingEvent)
class FeedingEventAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "feed_type", "quantity", "unit_price", "origin", "date")
    list_filter = ("origin", "feed_type")
