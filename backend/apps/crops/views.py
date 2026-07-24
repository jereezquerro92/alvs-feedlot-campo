from rest_framework import mixins, viewsets
from rest_framework.response import Response

from apps.crops.models import Crop, Cutting, FieldTask, Pivot
from apps.crops.serializers import (
    CropSerializer,
    CuttingSerializer,
    CuttingWriteSerializer,
    FieldTaskSerializer,
    FieldTaskWriteSerializer,
    PivotSerializer,
)


class PivotViewSet(viewsets.ModelViewSet):
    queryset = Pivot.objects.all()
    serializer_class = PivotSerializer

    def get_queryset(self):
        qs = Pivot.objects.all()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs


class CropViewSet(viewsets.ModelViewSet):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer

    def get_queryset(self):
        qs = Crop.objects.all()
        pivot_id = self.request.query_params.get("pivot")
        if pivot_id:
            qs = qs.filter(pivot_id=pivot_id)
        return qs


class CuttingViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    serializer_class = CuttingSerializer

    def get_queryset(self):
        qs = Cutting.objects.all()
        crop_id = self.request.query_params.get("crop")
        if crop_id:
            qs = qs.filter(crop_id=crop_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = CuttingWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)


class FieldTaskViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    serializer_class = FieldTaskSerializer

    def get_queryset(self):
        qs = FieldTask.objects.all()
        pivot_id = self.request.query_params.get("pivot")
        client_id = self.request.query_params.get("client")
        if pivot_id:
            qs = qs.filter(pivot_id=pivot_id)
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = FieldTaskWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)
