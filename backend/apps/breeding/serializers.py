"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import serializers

from apps.genetics.models import EmbryoBatch, SemenBatch, Sire
from apps.livestock.models import Animal, Lot
from apps.breeding.models import (
    Calving,
    CalvingEase,
    CalvingOutcome,
    IatfProtocol,
    IatfProtocolStep,
    Method,
    PregnancyCheck,
    PregnancyMethod,
    PregnancyResult,
    Service,
    Weaning,
    WeaningPurpose,
)
from apps.breeding.services import (
    register_calving,
    register_pregnancy_check,
    register_service,
    register_weaning,
)


# --- IATF template: editable catalog, full CRUD (adr-46 decision 5) -----------


class IatfProtocolStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = IatfProtocolStep
        fields = ["id", "protocol", "day_offset", "action", "product", "note"]


class IatfProtocolSerializer(serializers.ModelSerializer):
    steps = IatfProtocolStepSerializer(many=True, read_only=True)

    class Meta:
        model = IatfProtocol
        fields = ["id", "name", "description", "is_active", "steps"]


# --- reproductive events: read + write through the service (adr-46 decision 7) -


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = [
            "id", "animal", "lot", "client", "date", "method", "sire",
            "semen_batch", "embryo_batch", "protocol", "service_price", "note",
            "created_at",
        ]
        read_only_fields = fields


class ServiceWriteSerializer(serializers.Serializer):
    """A service is created through the service layer so the XOR, active-target,
    in-stock/active-batch gates and the single ledger write run atomically
    (adr-46 decisions 6-7)."""

    animal = serializers.PrimaryKeyRelatedField(
        queryset=Animal.objects.all(), required=False, allow_null=True
    )
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )
    date = serializers.DateField()
    method = serializers.ChoiceField(choices=Method.choices)
    sire = serializers.PrimaryKeyRelatedField(
        queryset=Sire.objects.all(), required=False, allow_null=True
    )
    semen_batch = serializers.PrimaryKeyRelatedField(
        queryset=SemenBatch.objects.all(), required=False, allow_null=True
    )
    embryo_batch = serializers.PrimaryKeyRelatedField(
        queryset=EmbryoBatch.objects.all(), required=False, allow_null=True
    )
    protocol = serializers.PrimaryKeyRelatedField(
        queryset=IatfProtocol.objects.all(), required=False, allow_null=True
    )
    service_price = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated):
        return ServiceSerializer(
            register_service(created_by=_actor(self), **validated)
        ).data

    def to_representation(self, instance):
        return instance


class PregnancyCheckSerializer(serializers.ModelSerializer):
    estimated_calving_date = serializers.DateField(read_only=True)

    class Meta:
        model = PregnancyCheck
        fields = [
            "id", "animal", "lot", "client", "date", "method", "result",
            "gestation_days", "service", "estimated_calving_date", "note",
            "created_at",
        ]
        read_only_fields = fields


class PregnancyCheckWriteSerializer(serializers.Serializer):
    animal = serializers.PrimaryKeyRelatedField(
        queryset=Animal.objects.all(), required=False, allow_null=True
    )
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )
    date = serializers.DateField()
    method = serializers.ChoiceField(choices=PregnancyMethod.choices)
    result = serializers.ChoiceField(choices=PregnancyResult.choices)
    gestation_days = serializers.IntegerField(required=False, allow_null=True)
    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), required=False, allow_null=True
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated):
        return PregnancyCheckSerializer(
            register_pregnancy_check(created_by=_actor(self), **validated)
        ).data

    def to_representation(self, instance):
        return instance


class CalvingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calving
        fields = [
            "id", "animal", "lot", "client", "date", "outcome", "calving_ease",
            "calf_sex", "calf_weight", "births_count", "service", "calf", "note",
            "created_at",
        ]
        read_only_fields = fields


class CalvingWriteSerializer(serializers.Serializer):
    """A live individual calving creates the calf Animal in the service (decision 4)."""

    animal = serializers.PrimaryKeyRelatedField(
        queryset=Animal.objects.all(), required=False, allow_null=True
    )
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )
    date = serializers.DateField()
    outcome = serializers.ChoiceField(choices=CalvingOutcome.choices)
    calving_ease = serializers.ChoiceField(
        choices=CalvingEase.choices, required=False, default=CalvingEase.NORMAL
    )
    calf_sex = serializers.CharField(required=False, allow_blank=True, default="")
    calf_weight = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True
    )
    births_count = serializers.IntegerField(required=False, allow_null=True)
    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), required=False, allow_null=True
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated):
        return CalvingSerializer(
            register_calving(created_by=_actor(self), **validated)
        ).data

    def to_representation(self, instance):
        return instance


class WeaningSerializer(serializers.ModelSerializer):
    class Meta:
        model = Weaning
        fields = [
            "id", "animal", "lot", "client", "date", "weaning_weight", "purpose",
            "note", "created_at",
        ]
        read_only_fields = fields


class WeaningWriteSerializer(serializers.Serializer):
    animal = serializers.PrimaryKeyRelatedField(
        queryset=Animal.objects.all(), required=False, allow_null=True
    )
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )
    date = serializers.DateField()
    weaning_weight = serializers.DecimalField(max_digits=8, decimal_places=2)
    purpose = serializers.ChoiceField(
        choices=WeaningPurpose.choices, required=False, default=WeaningPurpose.UNDECIDED
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated):
        return WeaningSerializer(
            register_weaning(created_by=_actor(self), **validated)
        ).data

    def to_representation(self, instance):
        return instance


def _actor(serializer):
    """The authenticated user behind the request, or None (an event may be created
    by a management command with no request)."""
    request = serializer.context.get("request")
    user = getattr(request, "user", None)
    if user is not None and not user.is_authenticated:
        return None
    return user
