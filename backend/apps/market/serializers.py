from rest_framework import serializers

from apps.market.models import MarketPrice, MarketSource
from apps.market.services import register_manual_price


class MarketSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketSource
        fields = ["id", "name", "slug", "kind", "is_active", "is_automated", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]


class MarketPriceSerializer(serializers.ModelSerializer):
    source_slug = serializers.CharField(source="source.slug", read_only=True)

    class Meta:
        model = MarketPrice
        fields = [
            "id", "source", "source_slug", "category", "date",
            "price_avg", "price_min", "price_max", "price_median", "head_count",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class ManualPriceSerializer(serializers.Serializer):
    """Manual load goes through the service so idempotency is respected."""

    source = serializers.SlugRelatedField(slug_field="slug", queryset=MarketSource.objects.all())
    category = serializers.CharField(max_length=60)
    date = serializers.DateField()
    price_avg = serializers.DecimalField(max_digits=14, decimal_places=4)
    price_min = serializers.DecimalField(max_digits=14, decimal_places=4, required=False, allow_null=True)
    price_max = serializers.DecimalField(max_digits=14, decimal_places=4, required=False, allow_null=True)
    price_median = serializers.DecimalField(max_digits=14, decimal_places=4, required=False, allow_null=True)
    head_count = serializers.IntegerField(required=False, allow_null=True, min_value=0)

    def create(self, validated):
        price = register_manual_price(**validated)
        return MarketPriceSerializer(price).data

    def to_representation(self, instance):
        return instance
