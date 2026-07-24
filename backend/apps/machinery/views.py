from rest_framework import mixins, viewsets
from rest_framework.response import Response

from apps.machinery.models import Machine, MaintenanceEvent
from apps.machinery.serializers import (
    MachineSerializer,
    MaintenanceEventSerializer,
    MaintenanceEventWriteSerializer,
)


class MachineViewSet(viewsets.ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer

    def get_queryset(self):
        qs = Machine.objects.all()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs


class MaintenanceEventViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    serializer_class = MaintenanceEventSerializer

    def get_queryset(self):
        qs = MaintenanceEvent.objects.all()
        machine_id = self.request.query_params.get("machine")
        client_id = self.request.query_params.get("client")
        if machine_id:
            qs = qs.filter(machine_id=machine_id)
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = MaintenanceEventWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)
