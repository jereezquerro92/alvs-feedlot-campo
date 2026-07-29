"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import serializers

from apps.clients.models import Client
from apps.expenses.models import ExpenseEvent
from apps.expenses.services import register_expense
from apps.livestock.models import Lot


class ExpenseEventSerializer(serializers.ModelSerializer):
    total_cost = serializers.DecimalField(
        max_digits=16, decimal_places=2, read_only=True
    )

    class Meta:
        model = ExpenseEvent
        fields = [
            "id", "client", "lot", "date", "title", "category",
            "fuel_kind", "unit_price", "quantity", "description",
            "total_cost", "created_at",
        ]
        read_only_fields = ["id", "total_cost", "created_at"]


class ExpenseEventWriteSerializer(serializers.Serializer):
    """Write path goes through the service so the `service` debit is never skipped."""

    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )
    date = serializers.DateField()
    title = serializers.CharField(max_length=120)
    category = serializers.ChoiceField(
        choices=ExpenseEvent.Category.choices, required=False,
        default=ExpenseEvent.Category.OTHER,
    )
    fuel_kind = serializers.CharField(max_length=32, required=False, allow_blank=True)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=4)
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, default=1
    )
    description = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )

    def create(self, validated):
        expense = register_expense(**validated)
        return ExpenseEventSerializer(expense).data

    def to_representation(self, instance):
        return instance
