from django.contrib import admin

from apps.weather.models import WeatherLog


@admin.register(WeatherLog)
class WeatherLogAdmin(admin.ModelAdmin):
    list_display = ("id", "site", "date", "rainfall_mm", "temp_min", "temp_max")
    list_filter = ("site",)
    date_hierarchy = "date"
    readonly_fields = tuple(f.name for f in WeatherLog._meta.fields)
