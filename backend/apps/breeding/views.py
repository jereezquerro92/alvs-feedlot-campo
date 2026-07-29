"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import mixins, viewsets

from apps.users.roles import BreedingAccess
from apps.breeding.models import (
    Calving,
    IatfProtocol,
    IatfProtocolStep,
    PregnancyCheck,
    Service,
    Weaning,
)
from apps.breeding.serializers import (
    CalvingSerializer,
    CalvingWriteSerializer,
    IatfProtocolSerializer,
    IatfProtocolStepSerializer,
    PregnancyCheckSerializer,
    PregnancyCheckWriteSerializer,
    ServiceSerializer,
    ServiceWriteSerializer,
    WeaningSerializer,
    WeaningWriteSerializer,
)


class _EventViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Reproductive events are immutable: list/retrieve/create only, no update or
    destroy (adr-24 rule 3). Writes route through the service via the write
    serializer; reads use the model serializer."""

    permission_classes = [BreedingAccess]
    read_serializer_class = None
    write_serializer_class = None

    def get_serializer_class(self):
        if self.action == "create":
            return self.write_serializer_class
        return self.read_serializer_class

    def get_queryset(self):
        qs = self.queryset
        params = self.request.query_params
        client = params.get("client")
        if client:
            qs = qs.filter(client_id=client)
        animal = params.get("animal")
        if animal:
            qs = qs.filter(animal_id=animal)
        lot = params.get("lot")
        if lot:
            qs = qs.filter(lot_id=lot)
        return qs


class ServiceViewSet(_EventViewSet):
    queryset = Service.objects.all()
    read_serializer_class = ServiceSerializer
    write_serializer_class = ServiceWriteSerializer


class PregnancyCheckViewSet(_EventViewSet):
    queryset = PregnancyCheck.objects.all()
    read_serializer_class = PregnancyCheckSerializer
    write_serializer_class = PregnancyCheckWriteSerializer


class CalvingViewSet(_EventViewSet):
    queryset = Calving.objects.all()
    read_serializer_class = CalvingSerializer
    write_serializer_class = CalvingWriteSerializer


class WeaningViewSet(_EventViewSet):
    queryset = Weaning.objects.all()
    read_serializer_class = WeaningSerializer
    write_serializer_class = WeaningWriteSerializer


class IatfProtocolViewSet(viewsets.ModelViewSet):
    """Editable IATF template — full CRUD master data (adr-46 decision 5)."""

    queryset = IatfProtocol.objects.all()
    serializer_class = IatfProtocolSerializer
    permission_classes = [BreedingAccess]


class IatfProtocolStepViewSet(viewsets.ModelViewSet):
    queryset = IatfProtocolStep.objects.all()
    serializer_class = IatfProtocolStepSerializer
    permission_classes = [BreedingAccess]

    def get_queryset(self):
        qs = self.queryset
        protocol = self.request.query_params.get("protocol")
        if protocol:
            qs = qs.filter(protocol_id=protocol)
        return qs
