"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import serializers

from apps.clients.models import Client
from apps.inventory.models import InputStockMovement, InputType, OwnerKind
from apps.inventory.services import register_input_movement


class InputTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InputType
        fields = ["id", "name", "unit", "category", "is_active"]


class InputStockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InputStockMovement
        fields = [
            "id", "owner_kind", "client", "input_type", "direction", "quantity",
            "unit_price", "date", "note", "source_kind", "source_id", "created_at",
        ]
        read_only_fields = fields


class InputStockMovementWriteSerializer(serializers.Serializer):
    """Creating a movement goes through the service so the catalog gate and the
    positivity check run in one atomic step (adr-37 decision 4)."""

    input_type = serializers.PrimaryKeyRelatedField(queryset=InputType.objects.all())
    direction = serializers.ChoiceField(choices=InputStockMovement.Direction.choices)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    date = serializers.DateField()
    owner_kind = serializers.ChoiceField(
        choices=OwnerKind.choices, default=OwnerKind.OWN
    )
    client = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), required=False, allow_null=True
    )
    unit_price = serializers.DecimalField(
        max_digits=14, decimal_places=4, required=False, allow_null=True
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated):
        request = self.context.get("request")
        created_by = getattr(request, "user", None)
        if created_by is not None and not created_by.is_authenticated:
            created_by = None
        movement = register_input_movement(created_by=created_by, **validated)
        return InputStockMovementSerializer(movement).data

    def to_representation(self, instance):
        return instance
