"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.clients.models import Account, Client
from apps.clients.serializers import AccountSerializer, ClientSerializer
from apps.ledger.models import LedgerEntry
from apps.ledger.serializers import LedgerEntrySerializer
from apps.ledger.services import outstanding_charges
from apps.users.roles import ClientDirectoryAccess, ClientScopedReadPermission


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.select_related("account").all()
    serializer_class = ClientSerializer

    def get_permissions(self):
        # The per-client account views are the routes a lot_owner may reach,
        # scoped to their own bound Client (adr-44 decision 3). The client
        # directory itself is staff-only read + field-manager write.
        if self.action in ("account", "ledger", "outstanding"):
            return [ClientScopedReadPermission()]
        return [ClientDirectoryAccess()]

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

    @action(detail=True, methods=["get"])
    def outstanding(self, request, pk=None):
        """Per-charge outstanding, derived on read (adr-41 decision 4)."""
        account = Account.objects.get(client_id=pk)
        return Response(outstanding_charges(account))
