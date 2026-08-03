"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import serializers

from apps.fx.models import FxRate
from apps.fx.services import register_fx_rate


class FxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FxRate
        fields = ["id", "currency", "date", "rate", "source", "created_at", "updated_at"]
        read_only_fields = fields


class FxRateWriteSerializer(serializers.Serializer):
    """Creating a rate goes through the service so the upsert and the positivity check
    run in one atomic step (adr-39 decision 2)."""

    currency = serializers.CharField(max_length=8)
    date = serializers.DateField()
    rate = serializers.DecimalField(max_digits=18, decimal_places=6)
    source = serializers.CharField(max_length=40, required=False, default="manual")

    def create(self, validated):
        rate = register_fx_rate(**validated)
        return FxRateSerializer(rate).data

    def to_representation(self, instance):
        return instance
