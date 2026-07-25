from rest_framework import mixins, viewsets

from apps.inventory.models import InputStockMovement, InputType
from apps.inventory.serializers import (
    InputStockMovementSerializer,
    InputStockMovementWriteSerializer,
    InputTypeSerializer,
)


class InputTypeViewSet(viewsets.ModelViewSet):
    """Editable input catalog — full CRUD (adr-37 decision 2)."""

    queryset = InputType.objects.all()
    serializer_class = InputTypeSerializer


class InputStockMovementViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.CreateModelMixin, viewsets.GenericViewSet,
):
    """Immutable stock movements. list/retrieve/create; no update/destroy — a
    correction is another movement (adr-37 decision 2)."""

    def get_serializer_class(self):
        if self.action == "create":
            return InputStockMovementWriteSerializer
        return InputStockMovementSerializer

    def get_queryset(self):
        qs = InputStockMovement.objects.select_related("input_type", "client")
        params = self.request.query_params
        if params.get("input_type"):
            qs = qs.filter(input_type_id=params["input_type"])
        if params.get("owner_kind"):
            qs = qs.filter(owner_kind=params["owner_kind"])
        if params.get("client"):
            qs = qs.filter(client_id=params["client"])
        return qs
