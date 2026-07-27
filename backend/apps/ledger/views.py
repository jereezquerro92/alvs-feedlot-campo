"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from apps.ledger.models import LedgerEntry, Payment, PaymentAllocation
from apps.ledger.serializers import (
    LedgerEntrySerializer,
    PaymentAllocationSerializer,
    PaymentAllocationWriteSerializer,
    PaymentSerializer,
)
from apps.users.roles import LedgerReadAccess, LedgerWriteAccess


class LedgerEntryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Entries are immutable — read-only over HTTP (adr-25 rule 1)."""

    permission_classes = [LedgerReadAccess]
    serializer_class = LedgerEntrySerializer

    def get_queryset(self):
        qs = LedgerEntry.objects.all()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(account__client_id=client_id)
        return qs


class PaymentViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    permission_classes = [LedgerWriteAccess]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        qs = Payment.objects.all()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(account__client_id=client_id)
        return qs


class PaymentAllocationViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Payment→charge imputation (adr-41). Immutable: create/list/retrieve only —
    a wrong imputation is corrected by another allocation (decision 5)."""

    permission_classes = [LedgerWriteAccess]

    def get_queryset(self):
        qs = PaymentAllocation.objects.select_related("payment", "entry").all()
        client_id = self.request.query_params.get("client")
        payment_id = self.request.query_params.get("payment")
        if client_id:
            qs = qs.filter(entry__account__client_id=client_id)
        if payment_id:
            qs = qs.filter(payment_id=payment_id)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentAllocationWriteSerializer
        return PaymentAllocationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=status.HTTP_201_CREATED)
