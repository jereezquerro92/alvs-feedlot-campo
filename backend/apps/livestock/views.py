from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.livestock.models import Animal, Death, Exit, Intake, Lot, Weighing
from apps.livestock.serializers import (
    AnimalSerializer,
    DeathSerializer,
    DeathWriteSerializer,
    ExitSerializer,
    ExitWriteSerializer,
    IntakeSerializer,
    LotSerializer,
    WeighingSerializer,
    WeighingWriteSerializer,
)
from apps.livestock.services import growth_series


class AnimalViewSet(viewsets.ModelViewSet):
    serializer_class = AnimalSerializer

    def get_queryset(self):
        qs = Animal.objects.all()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs

    @action(detail=True, methods=["get"])
    def growth(self, request, pk=None):
        """Weighing series with ADG between consecutive readings."""
        return Response(growth_series(animal=self.get_object()))


class LotViewSet(viewsets.ModelViewSet):
    serializer_class = LotSerializer

    def get_queryset(self):
        qs = Lot.objects.all()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs

    @action(detail=True, methods=["get"])
    def growth(self, request, pk=None):
        """ADG on weight per head — never on the lot total (see adr-28)."""
        return Response(growth_series(lot=self.get_object()))


class IntakeViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Intake.objects.all()
    serializer_class = IntakeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=201)


class _EventViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """Read freely, write only through the service — never a bare ModelSerializer.

    Lifecycle events are immutable: no update, no destroy on purpose.
    """

    model = None
    write_serializer_class = None

    def get_queryset(self):
        qs = self.model.objects.all()
        for param, field in (("animal", "animal_id"), ("lot", "lot_id")):
            value = self.request.query_params.get(param)
            if value:
                qs = qs.filter(**{field: value})
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.write_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save(), status=201)


class WeighingViewSet(_EventViewSet):
    model = Weighing
    serializer_class = WeighingSerializer
    write_serializer_class = WeighingWriteSerializer


class DeathViewSet(_EventViewSet):
    model = Death
    serializer_class = DeathSerializer
    write_serializer_class = DeathWriteSerializer


class ExitViewSet(_EventViewSet):
    model = Exit
    serializer_class = ExitSerializer
    write_serializer_class = ExitWriteSerializer
