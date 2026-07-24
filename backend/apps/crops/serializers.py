from rest_framework import serializers

from apps.clients.models import Client
from apps.crops.models import Crop, Cutting, FieldTask, Pivot
from apps.crops.services import register_cutting, register_field_task


class PivotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pivot
        fields = [
            "id", "client", "name", "code", "area_ha", "status",
            "acquired_date", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = [
            "id", "pivot", "species", "sown_date", "status", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CuttingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cutting
        fields = [
            "id", "crop", "date", "kg_harvested", "bales", "quality",
            "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CuttingWriteSerializer(serializers.Serializer):
    """Write path goes through the service (no ledger entry, adr-32 decision 4)."""

    crop = serializers.PrimaryKeyRelatedField(queryset=Crop.objects.all())
    date = serializers.DateField()
    kg_harvested = serializers.DecimalField(max_digits=12, decimal_places=2)
    bales = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    quality = serializers.CharField(max_length=8, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def create(self, validated):
        cutting = register_cutting(**validated)
        return CuttingSerializer(cutting).data

    def to_representation(self, instance):
        return instance


class FieldTaskSerializer(serializers.ModelSerializer):
    total_cost = serializers.DecimalField(
        max_digits=16, decimal_places=2, read_only=True
    )

    class Meta:
        model = FieldTask
        fields = [
            "id", "client", "pivot", "date", "title", "category",
            "unit_price", "quantity", "description", "total_cost", "created_at",
        ]
        read_only_fields = ["id", "total_cost", "created_at"]


class FieldTaskWriteSerializer(serializers.Serializer):
    """Write path goes through the service so the `service` debit is never skipped."""

    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    pivot = serializers.PrimaryKeyRelatedField(queryset=Pivot.objects.all())
    date = serializers.DateField()
    title = serializers.CharField(max_length=120)
    category = serializers.ChoiceField(
        choices=FieldTask.Category.choices, required=False,
        default=FieldTask.Category.OTHER,
    )
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=4)
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, default=1
    )
    description = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )

    def create(self, validated):
        task = register_field_task(**validated)
        return FieldTaskSerializer(task).data

    def to_representation(self, instance):
        return instance
