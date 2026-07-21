from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.clients.models import Account, Client
from apps.clients.serializers import AccountSerializer, ClientSerializer
from apps.ledger.models import LedgerEntry
from apps.ledger.serializers import LedgerEntrySerializer


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.select_related("account").all()
    serializer_class = ClientSerializer

    @action(detail=True, methods=["get"])
    def account(self, request, pk=None):
        account = Account.objects.get(client_id=pk)
        return Response(AccountSerializer(account).data)

    @action(detail=True, methods=["get"])
    def ledger(self, request, pk=None):
        entries = (
            LedgerEntry.objects.filter(account__client_id=pk)
            .order_by("-date", "-id")
        )
        return Response(LedgerEntrySerializer(entries, many=True).data)
