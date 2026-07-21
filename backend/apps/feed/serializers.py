from rest_framework import serializers

from apps.feed.models import FeedDelivery, FeedingEvent, FeedStockMovement, FeedType
from apps.feed.services import register_delivery, register_feeding


class FeedTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedType
        fields = ["id", "name", "unit", "category", "is_active"]
        read_only_fields = ["id"]


class FeedStockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedStockMovement
        fields = [
            "id", "owner_kind", "client", "feed_type", "direction",
            "quantity", "date", "source_kind", "source_id", "created_at",
        ]
        read_only_fields = fields


def _created_by(context):
    request = context.get("request")
    user = getattr(request, "user", None)
    return user if (user is not None and user.is_authenticated) else None


class FeedDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedDelivery
        fields = ["id", "client", "feed_type", "quantity", "date", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated):
        return register_delivery(created_by=_created_by(self.context), **validated)


class FeedingEventSerializer(serializers.ModelSerializer):
    total_cost = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = FeedingEvent
        fields = [
            "id", "client", "animal", "lot", "feed_type", "quantity",
            "unit_price", "origin", "date", "total_cost", "created_at",
        ]
        read_only_fields = ["id", "total_cost", "created_at"]

    def validate(self, attrs):
        if bool(attrs.get("animal")) == bool(attrs.get("lot")):
            raise serializers.ValidationError("Set exactly one of `animal` or `lot`.")
        return attrs

    def create(self, validated):
        return register_feeding(created_by=_created_by(self.context), **validated)
