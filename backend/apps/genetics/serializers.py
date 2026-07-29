"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import serializers

from apps.clients.models import Client
from apps.genetics.models import (
    BreedingValue,
    Direction,
    EmbryoBatch,
    EmbryoFlush,
    EmbryoMovement,
    EmbryoReason,
    SemenBatch,
    SemenMovement,
    SemenReason,
    SemenSale,
    Sire,
)
from apps.genetics.services import (
    register_embryo_flush,
    register_embryo_movement,
    register_semen_movement,
    register_semen_sale,
)
from apps.livestock.models import Animal


# --- catalogs: plain ModelSerializers, full CRUD (adr-47 decision 1) ---------


class SireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sire
        fields = ["id", "name", "breed", "animal", "registry_id", "is_active", "note"]


class BreedingValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreedingValue
        fields = ["id", "sire", "trait", "value", "accuracy", "source", "date"]


class SemenBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SemenBatch
        fields = [
            "id", "sire", "batch_code", "collection_date", "supplier", "tank",
            "position", "unit_cost", "expiry_date", "is_active", "note",
        ]


class EmbryoBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmbryoBatch
        fields = [
            "id", "donor", "sire", "grade", "flush_date", "tank", "position",
            "is_active", "note",
        ]


# --- events: read + write, the write serializer goes through the service -----


class SemenMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = SemenMovement
        fields = [
            "id", "semen_batch", "direction", "straws", "reason", "date",
            "source_kind", "source_id", "note", "created_at",
        ]
        read_only_fields = fields


class SemenMovementWriteSerializer(serializers.Serializer):
    """A movement is created through the service so the inactive-batch gate and the
    positivity check run in one atomic step (adr-47 decision 7)."""

    semen_batch = serializers.PrimaryKeyRelatedField(queryset=SemenBatch.objects.all())
    direction = serializers.ChoiceField(choices=Direction.choices)
    straws = serializers.DecimalField(max_digits=12, decimal_places=2)
    reason = serializers.ChoiceField(choices=SemenReason.choices)
    date = serializers.DateField()
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated):
        return SemenMovementSerializer(
            register_semen_movement(created_by=_actor(self), **validated)
        ).data

    def to_representation(self, instance):
        return instance


class SemenSaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SemenSale
        fields = [
            "id", "semen_batch", "date", "straws", "unit_price", "buyer_name",
            "buyer_client", "note", "created_at",
        ]
        read_only_fields = fields


class SemenSaleWriteSerializer(serializers.Serializer):
    """A sale posts a `sale` credit to the own account + an `out` movement in one
    transaction (adr-47 decision 4); the service gates stock and price."""

    semen_batch = serializers.PrimaryKeyRelatedField(queryset=SemenBatch.objects.all())
    date = serializers.DateField()
    straws = serializers.DecimalField(max_digits=12, decimal_places=2)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=4)
    buyer_name = serializers.CharField(required=False, allow_blank=True, default="")
    buyer_client = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), required=False, allow_null=True
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated):
        return SemenSaleSerializer(
            register_semen_sale(created_by=_actor(self), **validated)
        ).data

    def to_representation(self, instance):
        return instance


class EmbryoMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmbryoMovement
        fields = [
            "id", "embryo_batch", "direction", "quantity", "reason", "date",
            "source_kind", "source_id", "note", "created_at",
        ]
        read_only_fields = fields


class EmbryoMovementWriteSerializer(serializers.Serializer):
    embryo_batch = serializers.PrimaryKeyRelatedField(queryset=EmbryoBatch.objects.all())
    direction = serializers.ChoiceField(choices=Direction.choices)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    reason = serializers.ChoiceField(choices=EmbryoReason.choices)
    date = serializers.DateField()
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated):
        return EmbryoMovementSerializer(
            register_embryo_movement(created_by=_actor(self), **validated)
        ).data

    def to_representation(self, instance):
        return instance


class EmbryoFlushSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmbryoFlush
        fields = [
            "id", "donor", "sire", "date", "embryos_collected", "grade", "note",
            "created_at",
        ]
        read_only_fields = fields


class EmbryoFlushWriteSerializer(serializers.Serializer):
    """A flush creates/updates an EmbryoBatch and posts an `in` movement (decision 5)."""

    donor = serializers.PrimaryKeyRelatedField(queryset=Animal.objects.all())
    sire = serializers.PrimaryKeyRelatedField(
        queryset=Sire.objects.all(), required=False, allow_null=True
    )
    embryo_batch = serializers.PrimaryKeyRelatedField(
        queryset=EmbryoBatch.objects.all(), required=False, allow_null=True
    )
    date = serializers.DateField()
    embryos_collected = serializers.DecimalField(max_digits=12, decimal_places=2)
    grade = serializers.CharField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated):
        return EmbryoFlushSerializer(
            register_embryo_flush(created_by=_actor(self), **validated)
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
