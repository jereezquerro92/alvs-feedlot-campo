"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-51-api-and-backend]] · [[adr-53-api-membrane]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

"""Read-only metric endpoints, all scoped to one client (Phase 3)."""

from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.models import Client
from apps.metrics import services
from apps.users.roles import ClientScopedReadPermission, GeneticsAccess


def _period(request):
    """`?start=YYYY-MM-DD&end=YYYY-MM-DD`, both optional."""
    def parse(name):
        raw = request.query_params.get(name)
        return date.fromisoformat(raw) if raw else None

    return parse("start"), parse("end")


class _ClientMetricView(APIView):
    """Resolves the client and the period; subclasses just compute."""

    permission_classes = [ClientScopedReadPermission]

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


class ReproductionView(_ClientMetricView):
    """Derived reproductive metrics for one client (adr-46 decision 8)."""

    def compute(self, *, client, start, end):
        return services.reproduction(client=client, start=start, end=end)


class SemenStockView(APIView):
    """Derived semen stock (adr-47 decision 8). Not client-scoped — genetics is
    the feedyard's own asset. Optional `?sire=` and `?semen_batch=` filters and
    the `?start=&end=` period bound the per-sire usage."""

    permission_classes = [GeneticsAccess]

    def get(self, request):
        start, end = _period(request)
        params = request.query_params
        return Response(
            services.semen_stock_report(
                sire=params.get("sire") or None,
                semen_batch=params.get("semen_batch") or None,
                start=start,
                end=end,
            )
        )


class GrossMarginView(APIView):
    """Reference gross margin for one client (Phase 12, adr-39).

    Query: `?start=&end=&price_source=&category=&currency=`. `price_source` and
    `category` are required to price the produced kilos; `currency` is optional.
    """

    permission_classes = [ClientScopedReadPermission]

    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        start, end = _period(request)
        params = request.query_params
        return Response(
            services.gross_margin(
                client=client, start=start, end=end,
                price_source=params.get("price_source"),
                category=params.get("category"),
                currency=params.get("currency") or None,
                fx_source=params.get("fx_source") or None,
            )
        )
