"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import mixins, viewsets
from rest_framework.response import Response

from apps.advisors.models import Advisor, AdvisorReport
from apps.advisors.serializers import (
    AdvisorReportSerializer,
    AdvisorSerializer,
    GenerateReportSerializer,
)
from apps.users.roles import AdvisorAccess


class AdvisorViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [AdvisorAccess]
    queryset = Advisor.objects.all()
    serializer_class = AdvisorSerializer


class AdvisorReportViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """List/read stored reports; POST generates a new one (adr-27 rule 3: the
    report is the record — reads never re-run inference)."""

    permission_classes = [AdvisorAccess]
    serializer_class = AdvisorReportSerializer

    def get_queryset(self):
        qs = AdvisorReport.objects.select_related("advisor", "client")
        params = self.request.query_params
        if params.get("client"):
            qs = qs.filter(client_id=params["client"])
        if params.get("advisor"):
            qs = qs.filter(advisor__slug=params["advisor"])
        return qs

    def create(self, request, *args, **kwargs):
        serializer = GenerateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)
