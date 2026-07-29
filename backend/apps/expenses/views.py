"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from apps.expenses.models import ExpenseEvent
from apps.expenses.serializers import (
    ExpenseEventSerializer,
    ExpenseEventWriteSerializer,
)
from apps.users.roles import ExpensesAccess


class ExpenseEventViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """Extra expenses billed to a client (adr-44 decision 6). Immutable events:
    list/retrieve/create only — a fact is corrected by a new fact (adr-24 rule 3)."""

    permission_classes = [ExpensesAccess]
    serializer_class = ExpenseEventSerializer

    def get_queryset(self):
        qs = ExpenseEvent.objects.all()
        client_id = self.request.query_params.get("client")
        lot_id = self.request.query_params.get("lot")
        category = self.request.query_params.get("category")
        if client_id:
            qs = qs.filter(client_id=client_id)
        if lot_id:
            qs = qs.filter(lot_id=lot_id)
        if category:
            qs = qs.filter(category=category)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = ExpenseEventWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = serializer.save()
        except DjangoValidationError as exc:
            # Service-layer business rules (foreign lot, non-positive amounts)
            # surface as 400, not 500.
            raise DRFValidationError(exc.messages)
        return Response(data, status=201)
