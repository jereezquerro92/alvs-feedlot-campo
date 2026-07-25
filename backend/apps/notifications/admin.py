from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "channel", "to_address", "status", "created_at", "sent_at")
    list_filter = ("channel", "status")
    search_fields = ("to_address", "subject")
    readonly_fields = tuple(f.name for f in Notification._meta.fields)
