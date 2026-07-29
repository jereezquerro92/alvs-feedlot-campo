"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

from rest_framework import mixins, viewsets

from apps.genetics.models import (
    BreedingValue,
    EmbryoBatch,
    EmbryoFlush,
    EmbryoMovement,
    SemenBatch,
    SemenMovement,
    SemenSale,
    Sire,
)
from apps.genetics.serializers import (
    BreedingValueSerializer,
    EmbryoBatchSerializer,
    EmbryoFlushSerializer,
    EmbryoFlushWriteSerializer,
    EmbryoMovementSerializer,
    EmbryoMovementWriteSerializer,
    SemenBatchSerializer,
    SemenMovementSerializer,
    SemenMovementWriteSerializer,
    SemenSaleSerializer,
    SemenSaleWriteSerializer,
    SireSerializer,
)
from apps.users.roles import GeneticsAccess


class _EventViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """Immutable events: list/retrieve/create only — a correction is another event
    (adr-24 rule 3, adr-47 decision 1). The write serializer runs the service."""

    permission_classes = [GeneticsAccess]
    read_serializer_class = None
    write_serializer_class = None

    def get_serializer_class(self):
        if self.action == "create":
            return self.write_serializer_class
        return self.read_serializer_class


# --- catalogs: full CRUD (adr-47 decision 1) ---------------------------------


class SireViewSet(viewsets.ModelViewSet):
    permission_classes = [GeneticsAccess]
    queryset = Sire.objects.all()
    serializer_class = SireSerializer


class BreedingValueViewSet(viewsets.ModelViewSet):
    permission_classes = [GeneticsAccess]
    serializer_class = BreedingValueSerializer

    def get_queryset(self):
        qs = BreedingValue.objects.select_related("sire")
        sire = self.request.query_params.get("sire")
        if sire:
            qs = qs.filter(sire_id=sire)
        return qs


class SemenBatchViewSet(viewsets.ModelViewSet):
    permission_classes = [GeneticsAccess]
    serializer_class = SemenBatchSerializer

    def get_queryset(self):
        qs = SemenBatch.objects.select_related("sire")
        sire = self.request.query_params.get("sire")
        if sire:
            qs = qs.filter(sire_id=sire)
        return qs


class EmbryoBatchViewSet(viewsets.ModelViewSet):
    permission_classes = [GeneticsAccess]
    serializer_class = EmbryoBatchSerializer

    def get_queryset(self):
        qs = EmbryoBatch.objects.select_related("donor", "sire")
        donor = self.request.query_params.get("donor")
        if donor:
            qs = qs.filter(donor_id=donor)
        return qs


# --- events (adr-47 decision 1) ----------------------------------------------


class SemenMovementViewSet(_EventViewSet):
    read_serializer_class = SemenMovementSerializer
    write_serializer_class = SemenMovementWriteSerializer

    def get_queryset(self):
        qs = SemenMovement.objects.select_related("semen_batch")
        batch = self.request.query_params.get("semen_batch")
        if batch:
            qs = qs.filter(semen_batch_id=batch)
        return qs


class SemenSaleViewSet(_EventViewSet):
    read_serializer_class = SemenSaleSerializer
    write_serializer_class = SemenSaleWriteSerializer

    def get_queryset(self):
        qs = SemenSale.objects.select_related("semen_batch", "buyer_client")
        batch = self.request.query_params.get("semen_batch")
        if batch:
            qs = qs.filter(semen_batch_id=batch)
        return qs


class EmbryoMovementViewSet(_EventViewSet):
    read_serializer_class = EmbryoMovementSerializer
    write_serializer_class = EmbryoMovementWriteSerializer

    def get_queryset(self):
        qs = EmbryoMovement.objects.select_related("embryo_batch")
        batch = self.request.query_params.get("embryo_batch")
        if batch:
            qs = qs.filter(embryo_batch_id=batch)
        return qs


class EmbryoFlushViewSet(_EventViewSet):
    read_serializer_class = EmbryoFlushSerializer
    write_serializer_class = EmbryoFlushWriteSerializer

    def get_queryset(self):
        qs = EmbryoFlush.objects.select_related("donor", "sire")
        donor = self.request.query_params.get("donor")
        if donor:
            qs = qs.filter(donor_id=donor)
        return qs
