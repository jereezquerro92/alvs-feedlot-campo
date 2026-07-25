from rest_framework import serializers

from apps.feedyard.models import BunkScore, LoadingOrder, Pen, Ration, RationLine
from apps.feedyard.services import register_bunk_score, register_loading_order


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
