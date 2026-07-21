from rest_framework import serializers

from apps.clients.models import Client
from apps.livestock.models import Animal, Intake, Lot
from apps.livestock.services import create_individual_intake, create_lot_intake


class LotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lot
        fields = ["id", "client", "code", "mode", "head_count", "total_weight", "status", "created_at"]
        read_only_fields = ["id", "created_at"]


class AnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Animal
        fields = [
            "id", "client", "lot", "ear_tag", "category", "sex", "status",
            "entry_date", "entry_weight", "current_weight", "created_at",
        ]
        read_only_fields = ["id", "status", "current_weight", "created_at"]


class IntakeAnimalSerializer(serializers.Serializer):
    ear_tag = serializers.CharField(max_length=40)
    category = serializers.ChoiceField(choices=Animal._meta.get_field("category").choices)
    sex = serializers.CharField(max_length=6, required=False, allow_blank=True)
    entry_weight = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)


class IntakeSerializer(serializers.Serializer):
    """Write serializer for the intake event; dispatches on `mode` (adr-26 rule 1)."""

    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    date = serializers.DateField()
    mode = serializers.ChoiceField(choices=Intake.Mode.choices)
    # individual
    animals = IntakeAnimalSerializer(many=True, required=False)
    # lot
    code = serializers.CharField(max_length=40, required=False)
    head_count = serializers.IntegerField(required=False, min_value=1)
    total_weight = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

    def validate(self, attrs):
        if attrs["mode"] == Intake.Mode.INDIVIDUAL:
            if not attrs.get("animals"):
                raise serializers.ValidationError("Individual intake requires `animals`.")
        else:
            for f in ("code", "head_count", "total_weight"):
                if attrs.get(f) in (None, ""):
                    raise serializers.ValidationError(f"Lot intake requires `{f}`.")
        return attrs

    def create(self, validated):
        if validated["mode"] == Intake.Mode.INDIVIDUAL:
            intake, animals = create_individual_intake(
                client=validated["client"], date=validated["date"], animals=validated["animals"]
            )
            return {"intake": intake.id, "mode": "individual", "animals": [a.id for a in animals]}
        intake, lot = create_lot_intake(
            client=validated["client"],
            date=validated["date"],
            code=validated["code"],
            head_count=validated["head_count"],
            total_weight=validated["total_weight"],
        )
        return {"intake": intake.id, "mode": "lot", "lot": lot.id}

    def to_representation(self, instance):
        return instance
