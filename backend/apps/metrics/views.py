"""Read-only metric endpoints, all scoped to one client (Phase 3)."""

from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.models import Client
from apps.metrics import services


def _period(request):
    """`?start=YYYY-MM-DD&end=YYYY-MM-DD`, both optional."""
    def parse(name):
        raw = request.query_params.get(name)
        return date.fromisoformat(raw) if raw else None

    return parse("start"), parse("end")


class _ClientMetricView(APIView):
    """Resolves the client and the period; subclasses just compute."""

    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        start, end = _period(request)
        return Response(self.compute(client=client, start=start, end=end))

    def compute(self, *, client, start, end):  # pragma: no cover - abstract
        raise NotImplementedError


class SummaryView(_ClientMetricView):
    def compute(self, *, client, start, end):
        return services.summary(client=client, start=start, end=end)


class DailyCostView(_ClientMetricView):
    def compute(self, *, client, start, end):
        return services.daily_cost(client=client, start=start, end=end)


class GrowthView(_ClientMetricView):
    def compute(self, *, client, start, end):
        return services.kilos_gained(client=client, start=start, end=end)


class ConversionView(_ClientMetricView):
    def compute(self, *, client, start, end):
        return services.conversion(client=client, start=start, end=end)


class MortalityView(_ClientMetricView):
    def compute(self, *, client, start, end):
        return services.mortality(client=client, start=start, end=end)


class AccountEvolutionView(_ClientMetricView):
    def compute(self, *, client, start, end):
        return services.account_evolution(client=client, start=start, end=end)
