"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import serializers

from apps.feedyard.models import (
    BunkScore,
    LoadingOrder,
    Pen,
    PenPlacement,
    Ration,
    RationLine,
)
from apps.feedyard.services import (
    register_bunk_score,
    register_loading_order,
    register_placement,
)
from apps.livestock.models import Animal, Lot


def _created_by(context):
    request = context.get("request")
    user = getattr(request, "user", None)
    return user if (user is not None and user.is_authenticated) else None


class PenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pen
        fields = [
            "id", "code", "name", "capacity_head", "status", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RationLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = RationLine
        fields = ["id", "feed_type", "proportion", "dry_matter_pct"]
        read_only_fields = ["id"]


class RationSerializer(serializers.ModelSerializer):
    lines = RationLineSerializer(many=True, required=False)

    class Meta:
        model = Ration
        fields = ["id", "name", "description", "is_active", "lines", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated):
        lines = validated.pop("lines", [])
        ration = Ration.objects.create(**validated)
        for line in lines:
            RationLine.objects.create(ration=ration, **line)
        return ration

    def update(self, instance, validated):
        lines = validated.pop("lines", None)
        for attr, value in validated.items():
            setattr(instance, attr, value)
        instance.save()
        if lines is not None:
            instance.lines.all().delete()
            for line in lines:
                RationLine.objects.create(ration=instance, **line)
        return instance


class LoadingOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoadingOrder
        fields = [
            "id", "pen", "ration", "date", "planned_as_fed_kg", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class LoadingOrderWriteSerializer(serializers.Serializer):
    """Write path goes through the service (rejects inactive pen/ration; no ledger)."""

    pen = serializers.PrimaryKeyRelatedField(queryset=Pen.objects.all())
    ration = serializers.PrimaryKeyRelatedField(queryset=Ration.objects.all())
    date = serializers.DateField()
    planned_as_fed_kg = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def create(self, validated):
        order = register_loading_order(
            created_by=_created_by(self.context), **validated
        )
        return LoadingOrderSerializer(order).data

    def to_representation(self, instance):
        return instance


class BunkScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = BunkScore
        fields = ["id", "pen", "date", "score", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]


class BunkScoreWriteSerializer(serializers.Serializer):
    """Write path goes through the service (rejects inactive pen; validates 0–4)."""

    pen = serializers.PrimaryKeyRelatedField(queryset=Pen.objects.all())
    date = serializers.DateField()
    score = serializers.IntegerField(min_value=0, max_value=4)
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def create(self, validated):
        score = register_bunk_score(created_by=_created_by(self.context), **validated)
        return BunkScoreSerializer(score).data

    def to_representation(self, instance):
        return instance


class PenPlacementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PenPlacement
        fields = [
            "id", "pen", "animal", "lot", "date", "direction",
            "head_count", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PenPlacementWriteSerializer(serializers.Serializer):
    """Write path goes through the service (rejects inactive pen / non-active animal;
    enforces the animal-XOR-lot target). Posts no ledger entry."""

    pen = serializers.PrimaryKeyRelatedField(queryset=Pen.objects.all())
    animal = serializers.PrimaryKeyRelatedField(
        queryset=Animal.objects.all(), required=False, allow_null=True
    )
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )
    date = serializers.DateField()
    direction = serializers.ChoiceField(choices=PenPlacement.Direction.choices)
    head_count = serializers.IntegerField(
        required=False, allow_null=True, min_value=0
    )
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        if bool(attrs.get("animal")) == bool(attrs.get("lot")):
            raise serializers.ValidationError("Set exactly one of `animal` or `lot`.")
        return attrs

    def create(self, validated):
        placement = register_placement(
            created_by=_created_by(self.context), **validated
        )
        return PenPlacementSerializer(placement).data

    def to_representation(self, instance):
        return instance
