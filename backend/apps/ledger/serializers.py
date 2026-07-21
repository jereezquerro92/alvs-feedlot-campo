from rest_framework import serializers

from apps.ledger.models import LedgerEntry, Payment
from apps.ledger.services import register_payment


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
