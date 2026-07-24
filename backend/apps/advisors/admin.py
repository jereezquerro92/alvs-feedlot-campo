from django.contrib import admin

from apps.advisors.models import Advisor, AdvisorReport


@admin.register(Advisor)
class AdvisorAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "is_active")
    list_filter = ("is_active",)


@admin.register(AdvisorReport)
class AdvisorReportAdmin(admin.ModelAdmin):
    list_display = ("id", "advisor", "client", "created_at", "model_id", "tokens", "latency_ms")
    list_filter = ("advisor", "created_at")
    readonly_fields = ("input_snapshot", "output", "model_id", "tokens", "latency_ms", "created_at")
    date_hierarchy = "created_at"
