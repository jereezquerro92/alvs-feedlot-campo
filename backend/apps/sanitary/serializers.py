from rest_framework import serializers

from apps.clients.models import Client
from apps.livestock.models import Animal, Lot
from apps.sanitary.models import HealthEvent, HealthProduct
from apps.sanitary.services import register_health_event


class HealthProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthProduct
        fields = ["id", "name", "kind", "unit", "unit_price", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class HealthEventSerializer(serializers.ModelSerializer):
    total_cost = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = HealthEvent
        fields = [
            "id", "client", "animal", "lot", "product", "quantity", "head_count",
            "unit_price", "date", "applied_by", "notes", "total_cost", "created_at",
        ]
        read_only_fields = ["id", "unit_price", "total_cost", "created_at"]


class HealthEventWriteSerializer(serializers.Serializer):
    """Write path goes through the service so the ledger entry is never skipped."""

    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=HealthProduct.objects.all())
    animal = serializers.PrimaryKeyRelatedField(
        queryset=Animal.objects.all(), required=False, allow_null=True
    )
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    head_count = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    unit_price = serializers.DecimalField(
        max_digits=14, decimal_places=4, required=False, allow_null=True
    )
    date = serializers.DateField()
    applied_by = serializers.CharField(max_length=120, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def create(self, validated):
        event = register_health_event(**validated)
        return HealthEventSerializer(event).data

    def to_representation(self, instance):
        return instance
