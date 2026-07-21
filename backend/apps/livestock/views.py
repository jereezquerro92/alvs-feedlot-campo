from rest_framework import mixins, viewsets
from rest_framework.response import Response

from apps.livestock.models import Animal, Intake, Lot
from apps.livestock.serializers import AnimalSerializer, IntakeSerializer, LotSerializer


class AnimalViewSet(viewsets.ModelViewSet):
    serializer_class = AnimalSerializer

    def get_queryset(self):
        qs = Animal.objects.all()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs


class LotViewSet(viewsets.ModelViewSet):
    serializer_class = LotSerializer

    def get_queryset(self):
        qs = Lot.objects.all()
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs


class IntakeViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Intake.objects.all()
    serializer_class = IntakeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=201)
