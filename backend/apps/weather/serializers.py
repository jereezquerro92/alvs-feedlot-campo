from rest_framework import serializers

from apps.weather.models import WeatherLog
from apps.weather.services import register_weather_log


class WeatherLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherLog
        fields = [
            "id", "site", "date", "rainfall_mm", "temp_min", "temp_max",
            "note", "created_at",
        ]
        read_only_fields = fields


class WeatherLogWriteSerializer(serializers.Serializer):
    """Creating a log goes through the service so the rainfall/temperature checks
    run in one atomic step (adr-37 decision 5)."""

    date = serializers.DateField()
    rainfall_mm = serializers.DecimalField(
        max_digits=7, decimal_places=1, required=False, default=0
    )
    site = serializers.CharField(required=False, allow_blank=True, default="")
    temp_min = serializers.DecimalField(
        max_digits=5, decimal_places=1, required=False, allow_null=True
    )
    temp_max = serializers.DecimalField(
        max_digits=5, decimal_places=1, required=False, allow_null=True
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated):
        request = self.context.get("request")
        created_by = getattr(request, "user", None)
        if created_by is not None and not created_by.is_authenticated:
            created_by = None
        log = register_weather_log(created_by=created_by, **validated)
        return WeatherLogSerializer(log).data

    def to_representation(self, instance):
        return instance
