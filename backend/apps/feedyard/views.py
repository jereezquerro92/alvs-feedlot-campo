from rest_framework import mixins, viewsets
from rest_framework.response import Response

from apps.feedyard.models import BunkScore, LoadingOrder, Pen, PenPlacement, Ration
from apps.feedyard.serializers import (
    BunkScoreSerializer,
    BunkScoreWriteSerializer,
    LoadingOrderSerializer,
    LoadingOrderWriteSerializer,
    PenPlacementSerializer,
    PenPlacementWriteSerializer,
    PenSerializer,
    RationSerializer,
)


class PenViewSet(viewsets.ModelViewSet):
    queryset = Pen.objects.all()
    serializer_class = PenSerializer

    def get_queryset(self):
        qs = Pen.objects.all()
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs


class RationViewSet(viewsets.ModelViewSet):
    queryset = Ration.objects.all()
    serializer_class = RationSerializer

    def get_queryset(self):
        return Ration.objects.prefetch_related("lines").all()


class LoadingOrderViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    serializer_class = LoadingOrderSerializer

    def get_queryset(self):
        qs = LoadingOrder.objects.all()
        pen_id = self.request.query_params.get("pen")
        if pen_id:
            qs = qs.filter(pen_id=pen_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = LoadingOrderWriteSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)


class BunkScoreViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    serializer_class = BunkScoreSerializer

    def get_queryset(self):
        qs = BunkScore.objects.all()
        pen_id = self.request.query_params.get("pen")
        if pen_id:
            qs = qs.filter(pen_id=pen_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = BunkScoreWriteSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)


class PenPlacementViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    serializer_class = PenPlacementSerializer

    def get_queryset(self):
        qs = PenPlacement.objects.all()
        for field in ("pen", "animal", "lot"):
            value = self.request.query_params.get(field)
            if value:
                qs = qs.filter(**{f"{field}_id": value})
        return qs

    def create(self, request, *args, **kwargs):
        serializer = PenPlacementWriteSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)
