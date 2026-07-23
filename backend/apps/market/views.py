from rest_framework import mixins, viewsets
from rest_framework.response import Response

from apps.market.models import MarketPrice, MarketSource
from apps.market.serializers import (
    ManualPriceSerializer,
    MarketPriceSerializer,
    MarketSourceSerializer,
)


class MarketSourceViewSet(viewsets.ModelViewSet):
    queryset = MarketSource.objects.all()
    serializer_class = MarketSourceSerializer


class MarketPriceViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """Read prices; POST loads one by hand (manual fallback)."""

    serializer_class = MarketPriceSerializer

    def get_queryset(self):
        qs = MarketPrice.objects.select_related("source")
        params = self.request.query_params
        if params.get("source"):
            qs = qs.filter(source__slug=params["source"])
        if params.get("category"):
            qs = qs.filter(category=params["category"])
        if params.get("date"):
            qs = qs.filter(date=params["date"])
        return qs

    def create(self, request, *args, **kwargs):
        serializer = ManualPriceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)
