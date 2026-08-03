"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import serializers

from apps.ledger.models import LedgerEntry, Payment, PaymentAllocation
from apps.ledger.services import impute_payment, register_payment


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = [
            "id", "account", "date", "direction", "amount", "concept",
            "source_kind", "source_id", "unit_price", "quantity",
            "description", "created_at",
        ]
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "account", "date", "amount", "method", "reference", "entry", "created_at"]
        read_only_fields = ["id", "entry", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        created_by = getattr(request, "user", None)
        if created_by is not None and not created_by.is_authenticated:
            created_by = None
        return register_payment(
            account=validated_data["account"],
            amount=validated_data["amount"],
            date=validated_data["date"],
            method=validated_data.get("method", "transfer"),
            reference=validated_data.get("reference", ""),
            created_by=created_by,
        )


class PaymentAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAllocation
        fields = ["id", "payment", "entry", "amount", "created_at"]
        read_only_fields = fields


class _AllocationLineSerializer(serializers.Serializer):
    entry = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)


class PaymentAllocationWriteSerializer(serializers.Serializer):
    """Impute a payment against charges (adr-41). Either pass explicit
    `allocations` `[{entry, amount}]`, or omit them and set `auto=true` for
    FIFO oldest-first. Service validation surfaces as HTTP 400."""

    payment = serializers.PrimaryKeyRelatedField(queryset=Payment.objects.all())
    allocations = _AllocationLineSerializer(many=True, required=False)
    auto = serializers.BooleanField(required=False, default=False)

    def create(self, validated_data):
        request = self.context.get("request")
        created_by = getattr(request, "user", None)
        if created_by is not None and not created_by.is_authenticated:
            created_by = None
        try:
            allocations = impute_payment(
                payment=validated_data["payment"],
                allocations=validated_data.get("allocations") or None,
                auto=validated_data.get("auto", False),
                created_by=created_by,
            )
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))
        return PaymentAllocationSerializer(allocations, many=True).data

    def to_representation(self, instance):
        return instance
