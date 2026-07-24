from rest_framework import serializers

from apps.clients.models import Client
from apps.machinery.models import Machine, MaintenanceEvent
from apps.machinery.services import register_maintenance


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = [
            "id", "client", "name", "code", "category", "status",
            "acquired_date", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MaintenanceEventSerializer(serializers.ModelSerializer):
    total_cost = serializers.DecimalField(
        max_digits=16, decimal_places=2, read_only=True
    )

    class Meta:
        model = MaintenanceEvent
        fields = [
            "id", "client", "machine", "date", "title", "kind", "hours",
            "unit_price", "quantity", "description", "total_cost", "created_at",
        ]
        read_only_fields = ["id", "total_cost", "created_at"]


class MaintenanceEventWriteSerializer(serializers.Serializer):
    """Write path goes through the service so the `service` debit is never skipped."""

    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    machine = serializers.PrimaryKeyRelatedField(queryset=Machine.objects.all())
    date = serializers.DateField()
    title = serializers.CharField(max_length=120)
    kind = serializers.ChoiceField(
        choices=MaintenanceEvent.Kind.choices, required=False,
        default=MaintenanceEvent.Kind.PREVENTIVE,
    )
    hours = serializers.DecimalField(
        max_digits=10, decimal_places=1, required=False, allow_null=True
    )
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=4)
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, default=1
    )
    description = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )

    def create(self, validated):
        event = register_maintenance(**validated)
        return MaintenanceEventSerializer(event).data

    def to_representation(self, instance):
        return instance
