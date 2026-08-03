"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from django.shortcuts import get_object_or_404
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.clients.models import Client
from apps.sanitary.models import (
    HealthEvent,
    HealthProduct,
    PlanEnrollment,
    SanitaryPlan,
    SanitaryPlanItem,
)
from apps.sanitary.serializers import (
    HealthEventSerializer,
    HealthEventWriteSerializer,
    HealthProductSerializer,
    PlanEnrollmentSerializer,
    PlanEnrollmentWriteSerializer,
    SanitaryPlanItemSerializer,
    SanitaryPlanSerializer,
)
from apps.sanitary.services import plan_schedule_for_client
from apps.users.roles import SanitaryAccess


class HealthProductViewSet(viewsets.ModelViewSet):
    permission_classes = [SanitaryAccess]
    queryset = HealthProduct.objects.all()
    serializer_class = HealthProductSerializer


class HealthEventViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    permission_classes = [SanitaryAccess]
    serializer_class = HealthEventSerializer

    def get_queryset(self):
        qs = HealthEvent.objects.all()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = HealthEventWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)


class SanitaryPlanViewSet(viewsets.ModelViewSet):
    """Editable catalog: the reusable plan template (adr-40 decision 1)."""

    permission_classes = [SanitaryAccess]
    queryset = SanitaryPlan.objects.prefetch_related("items__product").all()
    serializer_class = SanitaryPlanSerializer


class SanitaryPlanItemViewSet(viewsets.ModelViewSet):
    """Editable catalog line. Filterable by `?plan=` to read one plan's items."""

    permission_classes = [SanitaryAccess]
    serializer_class = SanitaryPlanItemSerializer

    def get_queryset(self):
        qs = SanitaryPlanItem.objects.select_related("product").all()
        plan_id = self.request.query_params.get("plan")
        if plan_id:
            qs = qs.filter(plan_id=plan_id)
        return qs


class PlanEnrollmentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """Immutable event (adr-40 decision 1): list/retrieve/create only. The derived
    calendar rides on the `schedule` action, never a stored field (decision 3)."""

    permission_classes = [SanitaryAccess]
    serializer_class = PlanEnrollmentSerializer

    def get_queryset(self):
        qs = PlanEnrollment.objects.select_related("plan").all()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = PlanEnrollmentWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)

    @action(detail=False, methods=["get"])
    def schedule(self, request):
        client = get_object_or_404(Client, pk=request.query_params.get("client"))
        as_of = request.query_params.get("as_of") or None
        return Response(plan_schedule_for_client(client, as_of=as_of))
