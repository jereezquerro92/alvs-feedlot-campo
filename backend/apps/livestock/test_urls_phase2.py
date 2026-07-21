"""The Phase 2 routers must actually build.

Added after a broken viewset shipped with every service test green: the suite
exercised services, nothing exercised URL resolution.
"""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "name,path",
    [
        ("weighing-list", "/api/weighings/"),
        ("death-list", "/api/deaths/"),
        ("exit-list", "/api/exits/"),
        ("health-product-list", "/api/health-products/"),
        ("health-event-list", "/api/health-events/"),
    ],
)
def test_phase2_routes_resolve(name, path):
    assert reverse(name) == path


def test_growth_actions_resolve():
    assert reverse("animal-growth", args=[1]) == "/api/animals/1/growth/"
    assert reverse("lot-growth", args=[1]) == "/api/lots/1/growth/"
