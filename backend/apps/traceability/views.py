"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import mixins, viewsets

from apps.traceability.models import Caravana, Establishment, TransitDocument
from apps.traceability.serializers import (
    CaravanaSerializer,
    CaravanaWriteSerializer,
    EstablishmentSerializer,
    TransitDocumentSerializer,
    TransitDocumentWriteSerializer,
)
from apps.users.roles import TraceabilityAccess


class EstablishmentViewSet(viewsets.ModelViewSet):
    """Editable RENSPA catalog — full CRUD (adr-38 decision 1)."""

    permission_classes = [TraceabilityAccess]
    queryset = Establishment.objects.all()
    serializer_class = EstablishmentSerializer


class TransitDocumentViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """Immutable DT-e documents. list/retrieve/create; a correction is a new record
    (adr-38 decision 1)."""

    permission_classes = [TraceabilityAccess]

    def get_serializer_class(self):
        if self.action == "create":
            return TransitDocumentWriteSerializer
        return TransitDocumentSerializer

    def get_queryset(self):
        qs = TransitDocument.objects.select_related("origin", "destination", "lot")
        params = self.request.query_params
        if params.get("origin"):
            qs = qs.filter(origin_id=params["origin"])
        if params.get("destination"):
            qs = qs.filter(destination_id=params["destination"])
        return qs


class CaravanaViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """Immutable caravanas. list/retrieve/create; no update/destroy (adr-38 decision 4)."""

    permission_classes = [TraceabilityAccess]

    def get_serializer_class(self):
        if self.action == "create":
            return CaravanaWriteSerializer
        return CaravanaSerializer

    def get_queryset(self):
        qs = Caravana.objects.select_related("animal")
        animal = self.request.query_params.get("animal")
        if animal:
            qs = qs.filter(animal_id=animal)
        return qs
