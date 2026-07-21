from decimal import Decimal

from rest_framework import mixins, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.feed.models import FeedDelivery, FeedingEvent, FeedType, OwnerKind
from apps.feed.serializers import (
    FeedDeliverySerializer,
    FeedingEventSerializer,
    FeedTypeSerializer,
)
from apps.feed.services import stock_balance


class FeedTypeViewSet(viewsets.ModelViewSet):
    queryset = FeedType.objects.all()
    serializer_class = FeedTypeSerializer


class FeedDeliveryViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = FeedDelivery.objects.all()
    serializer_class = FeedDeliverySerializer


class FeedingEventViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FeedingEventSerializer

    def get_queryset(self):
        qs = FeedingEvent.objects.all()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def feed_stock(request):
    """Derived stock balances by (owner_kind, client, feed_type)."""
    from apps.clients.models import Client

    client_id = request.query_params.get("client")
    client = Client.objects.filter(id=client_id).first() if client_id else None
    out = []
    for ft in FeedType.objects.filter(is_active=True):
        row = {
            "feed_type": ft.id,
            "name": ft.name,
            "unit": ft.unit,
            "own": stock_balance(feed_type=ft, owner_kind=OwnerKind.OWN),
        }
        if client is not None:
            row["client"] = stock_balance(
                feed_type=ft, owner_kind=OwnerKind.CLIENT, client=client
            )
        out.append(row)
    return Response(out)
