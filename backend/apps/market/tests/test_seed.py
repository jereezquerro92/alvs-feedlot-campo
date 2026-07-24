"""The four sources are seeded, and only canuelas/ipcva are automated."""

import pytest
from apps.market.models import MarketSource

pytestmark = pytest.mark.django_db


def test_four_sources_are_seeded():
    slugs = set(MarketSource.objects.values_list("slug", flat=True))
    assert {"canuelas", "ipcva", "rosgan", "manual"} <= slugs


def test_only_canuelas_and_ipcva_are_automated():
    automated = set(MarketSource.objects.filter(is_automated=True).values_list("slug", flat=True))
    assert automated == {"canuelas", "ipcva"}
