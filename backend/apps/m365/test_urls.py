"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

import httpx
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse
from rest_framework.permissions import AllowAny

from apps.m365 import graph, views


@pytest.fixture(autouse=True)
def _clear_cell_cache():
    graph._cell_cache.clear()
    graph._cache.update({"site_id": None, "item_id": None, "worksheet_name": None})
    yield
    graph._cell_cache.clear()
    graph._cache.update({"site_id": None, "item_id": None, "worksheet_name": None})


def test_two_routes_resolve():
    assert reverse("m365:hello") == "/api/m365/hello/"
    assert reverse("m365:world") == "/api/m365/world/"


def test_hello_world_are_allow_any_no_auth_classes():
    assert views.HelloView.permission_classes == [AllowAny]
    assert views.HelloView.authentication_classes == []
    assert views.WorldView.permission_classes == [AllowAny]
    assert views.WorldView.authentication_classes == []


def test_hello_returns_clean_502_when_token_acquisition_fails():
    client = Client()
    with patch("apps.m365.graph.acquire_access_token", side_effect=RuntimeError("boom")):
        response = client.get("/api/m365/hello/")
    assert response.status_code == 502
    assert response["Content-Type"].startswith("text/plain")
    assert response.content.decode() == "graph_auth_failed"
    assert response["Cache-Control"] == "no-store"


def test_world_returns_clean_502_when_token_acquisition_fails():
    client = Client()
    with patch("apps.m365.graph.acquire_access_token", side_effect=RuntimeError("boom")):
        response = client.get("/api/m365/world/")
    assert response.status_code == 502
    assert response.content.decode() == "graph_auth_failed"


def test_repeat_call_within_ttl_does_not_re_hit_graph():
    client = Client()
    with (
        patch("apps.m365.graph.acquire_access_token", return_value="tok"),
        patch("apps.m365.graph._get") as mock_get,
    ):
        mock_get.side_effect = [
            {"id": "site-1"},
            {"id": "item-1"},
            {"value": [{"name": "Sheet1"}]},
            {"values": [["hello"]]},
        ]
        first = client.get("/api/m365/hello/")
        second = client.get("/api/m365/hello/")

    assert first.status_code == 200
    assert first.content.decode() == "hello"
    assert second.status_code == 200
    assert second.content.decode() == "hello"
    assert first["Cache-Control"] == "no-store"
    # Only the first call performs the four Graph lookups (site, item,
    # worksheet, cell range); the second call is served from the
    # per-process cell cache with zero additional Graph hits.
    assert mock_get.call_count == 4


def _graph_status_error(status_code):
    request = httpx.Request("GET", "https://graph.microsoft.com/v1.0/test")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError("graph error", request=request, response=response)


@pytest.mark.parametrize("route", ["/api/m365/hello/", "/api/m365/world/"])
def test_graph_403_returns_clean_502_graph_forbidden(route):
    client = Client()
    with (
        patch("apps.m365.graph.acquire_access_token", return_value="tok"),
        patch("apps.m365.graph.get_cell", side_effect=_graph_status_error(403)),
    ):
        response = client.get(route)
    assert response.status_code == 502
    assert response.content.decode() == "graph_forbidden"
    assert response["Content-Type"].startswith("text/plain")
    assert response["Cache-Control"] == "no-store"


@pytest.mark.parametrize("route", ["/api/m365/hello/", "/api/m365/world/"])
def test_graph_429_returns_clean_503_graph_throttled(route):
    client = Client()
    with (
        patch("apps.m365.graph.acquire_access_token", return_value="tok"),
        patch("apps.m365.graph.get_cell", side_effect=_graph_status_error(429)),
    ):
        response = client.get(route)
    assert response.status_code == 503
    assert response.content.decode() == "graph_throttled"
    assert response["Content-Type"].startswith("text/plain")
    assert response["Cache-Control"] == "no-store"


@pytest.mark.parametrize("route", ["/api/m365/hello/", "/api/m365/world/"])
def test_graph_other_http_error_returns_clean_502_graph_error(route):
    client = Client()
    with (
        patch("apps.m365.graph.acquire_access_token", return_value="tok"),
        patch("apps.m365.graph.get_cell", side_effect=_graph_status_error(500)),
    ):
        response = client.get(route)
    assert response.status_code == 502
    assert response.content.decode() == "graph_error"
    assert response["Cache-Control"] == "no-store"


@pytest.mark.parametrize("route", ["/api/m365/hello/", "/api/m365/world/"])
def test_unexpected_exception_returns_clean_502_graph_error_no_traceback(route):
    client = Client()
    with (
        patch("apps.m365.graph.acquire_access_token", return_value="tok"),
        patch("apps.m365.graph.get_cell", side_effect=ValueError("unexpected")),
    ):
        response = client.get(route)
    assert response.status_code == 502
    assert response.content.decode() == "graph_error"
    assert response["Cache-Control"] == "no-store"
