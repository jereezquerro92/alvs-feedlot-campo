from rest_framework import serializers

from apps.advisors.models import Advisor, AdvisorReport
from apps.advisors.services import generate_report
from apps.clients.models import Client


class AdvisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advisor
        fields = ["id", "slug", "name", "system_prompt", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class AdvisorReportSerializer(serializers.ModelSerializer):
    advisor_slug = serializers.CharField(source="advisor.slug", read_only=True)

    class Meta:
        model = AdvisorReport
        fields = [
            "id", "advisor", "advisor_slug", "client", "period_start", "period_end",
            "input_snapshot", "output", "model_id", "tokens", "latency_ms", "created_at",
        ]
        read_only_fields = fields


class GenerateReportSerializer(serializers.Serializer):
    """Generation goes through the service so the snapshot is always backend-built."""

    advisor = serializers.SlugRelatedField(slug_field="slug", queryset=Advisor.objects.all())
    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    start = serializers.DateField(required=False, allow_null=True)
    end = serializers.DateField(required=False, allow_null=True)

    def create(self, validated):
        report = generate_report(
            advisor=validated["advisor"],
            client=validated["client"],
            start=validated.get("start"),
            end=validated.get("end"),
        )
        return AdvisorReportSerializer(report).data

    def to_representation(self, instance):
        return instance
