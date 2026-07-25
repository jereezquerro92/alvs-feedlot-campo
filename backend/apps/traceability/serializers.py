from rest_framework import serializers

from apps.livestock.models import Animal, Lot
from apps.traceability.models import Caravana, Establishment, TransitDocument
from apps.traceability.services import register_caravana, register_transit


class EstablishmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Establishment
        fields = ["id", "renspa", "name", "holder", "location", "is_active"]


class TransitDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransitDocument
        fields = [
            "id", "dte_number", "origin", "destination", "date", "category",
            "head_count", "total_weight", "lot", "note", "created_at",
        ]
        read_only_fields = fields


class TransitDocumentWriteSerializer(serializers.Serializer):
    """Creating a DT-e goes through the service so its gates run atomically (adr-38 decision 3)."""

    dte_number = serializers.CharField(max_length=40)
    origin = serializers.PrimaryKeyRelatedField(queryset=Establishment.objects.all())
    destination = serializers.PrimaryKeyRelatedField(queryset=Establishment.objects.all())
    date = serializers.DateField()
    head_count = serializers.IntegerField(min_value=1)
    category = serializers.ChoiceField(
        choices=TransitDocument.Category.choices,
        default=TransitDocument.Category.MIXED,
    )
    total_weight = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated):
        request = self.context.get("request")
        created_by = getattr(request, "user", None)
        if created_by is not None and not created_by.is_authenticated:
            created_by = None
        transit = register_transit(created_by=created_by, **validated)
        return TransitDocumentSerializer(transit).data

    def to_representation(self, instance):
        return instance


class CaravanaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caravana
        fields = ["id", "official_number", "animal", "assigned_date", "note", "created_at"]
        read_only_fields = fields


class CaravanaWriteSerializer(serializers.Serializer):
    """Creating a caravana goes through the service so its gates run atomically (adr-38 decision 4)."""

    official_number = serializers.CharField(max_length=40)
    animal = serializers.PrimaryKeyRelatedField(queryset=Animal.objects.all())
    assigned_date = serializers.DateField()
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated):
        request = self.context.get("request")
        created_by = getattr(request, "user", None)
        if created_by is not None and not created_by.is_authenticated:
            created_by = None
        caravana = register_caravana(created_by=created_by, **validated)
        return CaravanaSerializer(caravana).data

    def to_representation(self, instance):
        return instance
