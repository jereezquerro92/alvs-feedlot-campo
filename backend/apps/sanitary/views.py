from rest_framework import mixins, viewsets
from rest_framework.response import Response

from apps.sanitary.models import HealthEvent, HealthProduct
from apps.sanitary.serializers import (
    HealthEventSerializer,
    HealthEventWriteSerializer,
    HealthProductSerializer,
)


class HealthProductViewSet(viewsets.ModelViewSet):
    queryset = HealthProduct.objects.all()
    serializer_class = HealthProductSerializer


class HealthEventViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    serializer_class = HealthEventSerializer

    def get_queryset(self):
        qs = HealthEvent.objects.all()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = HealthEventWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)
