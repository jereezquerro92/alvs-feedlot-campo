"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

import io
import json
from unittest import mock

from django.urls import resolve

from config import settings

HEALTH_PATH = "/api/health/"


def _metadata_response(ip):
    payload = {"Networks": [{"IPv4Addresses": [ip]}]}
    return io.BytesIO(json.dumps(payload).encode())


def test_ecs_task_ip_reads_metadata_endpoint():
    with mock.patch.dict(
        "os.environ", {"ECS_CONTAINER_METADATA_URI_V4": "http://169.254.170.2/v4"}
    ), mock.patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value = _metadata_response("10.20.3.4")
        assert settings._ecs_task_ip() == "10.20.3.4"


def test_ecs_task_ip_none_without_env():
    with mock.patch.dict("os.environ", {}, clear=True):
        assert settings._ecs_task_ip() is None


def test_ecs_task_ip_fails_open_on_error():
    with mock.patch.dict(
        "os.environ", {"ECS_CONTAINER_METADATA_URI_V4": "http://169.254.170.2/v4"}
    ), mock.patch("urllib.request.urlopen", side_effect=OSError("boom")):
        assert settings._ecs_task_ip() is None


def test_allowed_hosts_unpolluted_without_metadata_env():
    assert "10.20.3.4" not in settings.ALLOWED_HOSTS


def test_health_returns_200(client):
    assert client.get(HEALTH_PATH).status_code == 200


def test_health_requires_no_auth(client):
    response = client.get(HEALTH_PATH)
    assert response.status_code == 200


def test_health_sets_explicit_cache_control(client):
    response = client.get(HEALTH_PATH)
    assert response.headers["Cache-Control"] == "no-store"


def test_health_body_reports_ok(client):
    response = client.get(HEALTH_PATH)
    assert response.json() == {"status": "ok"}


def test_health_url_resolves_to_view():
    from apps.health.views import HealthCheckView

    match = resolve(HEALTH_PATH)
    assert match.func.cls is HealthCheckView


def test_health_independent_of_database(client):
    assert client.get(HEALTH_PATH).status_code == 200
