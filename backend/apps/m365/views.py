"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-03-api-and-backend]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

"""Views for the m365 app-only Graph capability (adr-13-m365-graph).

hello/world are deliberately AllowAny with no session — a named, bounded
owner override (rule 3). Auth is app-only client_credentials (rule 1): no
user, no browser flow, no stored token — the access token is minted fresh
per request via msal and never persisted.
"""

import logging
from typing import final

import httpx
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView

from django.http import HttpResponse

from apps.m365 import graph

logger = logging.getLogger(__name__)

CELL_HELLO = "A1"
CELL_WORLD = "C3"


def _no_store_text(body: str, status: int = 200, content_type: str = "text/plain") -> HttpResponse:
    response = HttpResponse(body, status=status, content_type=content_type)
    response["Cache-Control"] = "no-store"
    return response


def _read_cell(address: str) -> HttpResponse:
    try:
        access_token = graph.acquire_access_token()
    except Exception:
        logger.exception("Graph app-only token acquisition failed for cell %s", address)
        return _no_store_text("graph_auth_failed", status=502)
    try:
        value: str = graph.get_cell(access_token, address)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 403:
            logger.warning("Graph request forbidden (403) for cell %s", address, exc_info=True)
            return _no_store_text("graph_forbidden", status=502)
        if exc.response.status_code == 429:
            logger.warning("Graph request throttled (429) for cell %s", address, exc_info=True)
            return _no_store_text("graph_throttled", status=503)
        logger.exception("Graph request failed with HTTP status error for cell %s", address)
        return _no_store_text("graph_error", status=502)
    except Exception:
        logger.exception("Graph request failed unexpectedly for cell %s", address)
        return _no_store_text("graph_error", status=502)
    return _no_store_text(value)


@final
class HelloView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request: Request) -> HttpResponse:
        return _read_cell(CELL_HELLO)


@final
class WorldView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request: Request) -> HttpResponse:
        return _read_cell(CELL_WORLD)
