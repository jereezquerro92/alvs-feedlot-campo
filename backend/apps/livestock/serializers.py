"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import serializers

from apps.clients.models import Client
from apps.livestock.models import Animal, Intake, Lot
from apps.livestock.services import (
    add_to_lot_intake,
    create_individual_intake,
    create_lot_intake,
)


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
    # lot: EITHER a new `code` (creates an anonymous lot) OR an existing `lot`
    # id (adds to that lot's counters, adr-26 rule 1 "creates or updates").
    code = serializers.CharField(max_length=40, required=False)
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )
    head_count = serializers.IntegerField(required=False, min_value=1)
    total_weight = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

    def validate(self, attrs):
        if attrs["mode"] == Intake.Mode.INDIVIDUAL:
            if not attrs.get("animals"):
                raise serializers.ValidationError("Individual intake requires `animals`.")
        else:
            for f in ("head_count", "total_weight"):
                if attrs.get(f) in (None, ""):
                    raise serializers.ValidationError(f"Lot intake requires `{f}`.")
            # Exactly one of: a new `code`, or an existing `lot`.
            has_code = attrs.get("code") not in (None, "")
            has_lot = attrs.get("lot") is not None
            if has_code == has_lot:
                raise serializers.ValidationError(
                    "Lot intake requires either a new `code` or an existing `lot`, not both."
                )
        return attrs

    def create(self, validated):
        if validated["mode"] == Intake.Mode.INDIVIDUAL:
            intake, animals = create_individual_intake(
                client=validated["client"], date=validated["date"], animals=validated["animals"]
            )
            return {"intake": intake.id, "mode": "individual", "animals": [a.id for a in animals]}
        if validated.get("lot") is not None:
            intake, lot = add_to_lot_intake(
                client=validated["client"],
                date=validated["date"],
                lot=validated["lot"],
                head_count=validated["head_count"],
                total_weight=validated["total_weight"],
            )
            return {"intake": intake.id, "mode": "lot", "lot": lot.id, "added": True}
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


# --- Phase 2: lifecycle ------------------------------------------------------

from apps.livestock.models import Death, Exit, Weighing
from apps.livestock.services import register_death, register_exit, register_weighing


class _TargetMixin(serializers.Serializer):
    """Animal XOR lot, validated before the service is reached."""

    animal = serializers.PrimaryKeyRelatedField(
        queryset=Animal.objects.all(), required=False, allow_null=True
    )
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )

    def validate(self, attrs):
        if bool(attrs.get("animal")) == bool(attrs.get("lot")):
            raise serializers.ValidationError("Indicar exactamente uno: `animal` o `lot`.")
        return attrs


class WeighingSerializer(serializers.ModelSerializer):
    weight_per_head = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Weighing
        fields = [
            "id", "animal", "lot", "date", "weight", "head_count",
            "method", "notes", "weight_per_head", "created_at",
        ]
        read_only_fields = ["id", "weight_per_head", "created_at"]


class WeighingWriteSerializer(_TargetMixin):
    date = serializers.DateField()
    weight = serializers.DecimalField(max_digits=12, decimal_places=2)
    head_count = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    method = serializers.ChoiceField(choices=Weighing.Method.choices, required=False)
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def create(self, validated):
        return WeighingSerializer(register_weighing(**validated)).data

    def to_representation(self, instance):
        return instance


class DeathSerializer(serializers.ModelSerializer):
    class Meta:
        model = Death
        fields = [
            "id", "animal", "lot", "date", "cause", "cause_detail",
            "head_count", "weight", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DeathWriteSerializer(_TargetMixin):
    date = serializers.DateField()
    cause = serializers.ChoiceField(choices=Death.Cause.choices, required=False)
    cause_detail = serializers.CharField(max_length=255, required=False, allow_blank=True)
    head_count = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    weight = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )

    def create(self, validated):
        return DeathSerializer(register_death(**validated)).data

    def to_representation(self, instance):
        return instance


class ExitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exit
        fields = [
            "id", "animal", "lot", "date", "kind", "destination",
            "head_count", "weight", "sale_price_per_kg",
            "engorde_commission_pct", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ExitWriteSerializer(_TargetMixin):
    date = serializers.DateField()
    kind = serializers.ChoiceField(choices=Exit.Kind.choices, required=False)
    destination = serializers.CharField(max_length=120, required=False, allow_blank=True)
    head_count = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    weight = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    sale_price_per_kg = serializers.DecimalField(
        max_digits=14, decimal_places=4, required=False, allow_null=True
    )
    # Boarding-only engorde commission percent (adr-43); own cattle ignore it.
    commission_pct = serializers.DecimalField(
        max_digits=6, decimal_places=3, required=False, allow_null=True
    )

    def create(self, validated):
        return ExitSerializer(register_exit(**validated)).data

    def to_representation(self, instance):
        return instance
