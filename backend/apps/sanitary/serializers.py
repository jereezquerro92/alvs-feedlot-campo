"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import serializers

from apps.clients.models import Client
from apps.livestock.models import Animal, Lot
from apps.sanitary.models import (
    HealthEvent,
    HealthProduct,
    PlanEnrollment,
    SanitaryPlan,
    SanitaryPlanItem,
)
from apps.sanitary.services import enroll_in_plan, register_health_event


class HealthProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthProduct
        fields = ["id", "name", "kind", "unit", "unit_price", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class HealthEventSerializer(serializers.ModelSerializer):
    total_cost = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = HealthEvent
        fields = [
            "id", "client", "animal", "lot", "product", "quantity", "head_count",
            "unit_price", "date", "applied_by", "notes", "total_cost", "created_at",
        ]
        read_only_fields = ["id", "unit_price", "total_cost", "created_at"]


class HealthEventWriteSerializer(serializers.Serializer):
    """Write path goes through the service so the ledger entry is never skipped."""

    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=HealthProduct.objects.all())
    animal = serializers.PrimaryKeyRelatedField(
        queryset=Animal.objects.all(), required=False, allow_null=True
    )
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    head_count = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    unit_price = serializers.DecimalField(
        max_digits=14, decimal_places=4, required=False, allow_null=True
    )
    date = serializers.DateField()
    applied_by = serializers.CharField(max_length=120, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def create(self, validated):
        event = register_health_event(**validated)
        return HealthEventSerializer(event).data

    def to_representation(self, instance):
        return instance


class SanitaryPlanItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SanitaryPlanItem
        fields = ["id", "plan", "product", "product_name", "day_offset", "dose", "notes"]
        read_only_fields = ["id"]


class SanitaryPlanSerializer(serializers.ModelSerializer):
    items = SanitaryPlanItemSerializer(many=True, read_only=True)

    class Meta:
        model = SanitaryPlan
        fields = ["id", "name", "description", "is_active", "items", "created_at"]
        read_only_fields = ["id", "items", "created_at"]


class PlanEnrollmentSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = PlanEnrollment
        fields = [
            "id", "plan", "plan_name", "client", "animal", "lot",
            "start_date", "notes", "created_at",
        ]
        read_only_fields = ["id", "plan_name", "created_at"]


class PlanEnrollmentWriteSerializer(serializers.Serializer):
    """Write path goes through the service so the XOR/active checks never get skipped."""

    plan = serializers.PrimaryKeyRelatedField(queryset=SanitaryPlan.objects.all())
    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    animal = serializers.PrimaryKeyRelatedField(
        queryset=Animal.objects.all(), required=False, allow_null=True
    )
    lot = serializers.PrimaryKeyRelatedField(
        queryset=Lot.objects.all(), required=False, allow_null=True
    )
    start_date = serializers.DateField()
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def create(self, validated):
        enrollment = enroll_in_plan(**validated)
        return PlanEnrollmentSerializer(enrollment).data

    def to_representation(self, instance):
        return instance
