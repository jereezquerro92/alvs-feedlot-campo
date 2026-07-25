"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import mixins, viewsets

from apps.weather.models import WeatherLog
from apps.weather.serializers import WeatherLogSerializer, WeatherLogWriteSerializer


class WeatherLogViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """Immutable per-date weather logs. list/retrieve/create; a correction is another
    record (adr-37 decision 5)."""

    def get_serializer_class(self):
        if self.action == "create":
            return WeatherLogWriteSerializer
        return WeatherLogSerializer

    def get_queryset(self):
        qs = WeatherLog.objects.all()
        site = self.request.query_params.get("site")
        if site is not None:
            qs = qs.filter(site=site)
        return qs
