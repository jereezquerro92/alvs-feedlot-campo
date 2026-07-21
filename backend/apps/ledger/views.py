from rest_framework import mixins, viewsets

from apps.ledger.models import LedgerEntry, Payment
from apps.ledger.serializers import LedgerEntrySerializer, PaymentSerializer


class LedgerEntryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Entries are immutable — read-only over HTTP (adr-25 rule 1)."""

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
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
