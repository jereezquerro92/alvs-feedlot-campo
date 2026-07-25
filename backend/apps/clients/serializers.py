"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import serializers

from apps.clients.models import Account, Client


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["client", "balance_cached", "updated_at"]
        read_only_fields = fields


class ClientSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(
        source="account.balance_cached",
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Client
        fields = ["id", "name", "kind", "tax_id", "contact", "is_active", "balance", "created_at"]
        read_only_fields = ["id", "balance", "created_at"]
