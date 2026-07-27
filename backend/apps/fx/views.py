"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import mixins, viewsets

from apps.fx.models import FxRate
from apps.fx.serializers import FxRateSerializer, FxRateWriteSerializer
from apps.users.roles import FxAccess


class FxRateViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """Read reference FX rates; POST upserts one by hand (adr-39 decision 2)."""

    permission_classes = [FxAccess]

    def get_serializer_class(self):
        if self.action == "create":
            return FxRateWriteSerializer
        return FxRateSerializer

    def get_queryset(self):
        qs = FxRate.objects.all()
        params = self.request.query_params
        if params.get("currency"):
            qs = qs.filter(currency=params["currency"])
        if params.get("source"):
            qs = qs.filter(source=params["source"])
        if params.get("date"):
            qs = qs.filter(date=params["date"])
        return qs
