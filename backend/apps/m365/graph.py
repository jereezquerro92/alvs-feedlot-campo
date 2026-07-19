"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-13-m365-graph]]
Docs: [[BACKEND]]
API: [[API]]
LIVE-DOC:END"""

"""Thin Microsoft Graph v1.0 client, app-only (adr-13-m365-graph).

Auth is client_credentials via msal's ConfidentialClientApplication, using
the `.default` scope — no user, no browser, no stored token. msal keeps its
own in-memory token cache and handles renewal transparently across calls;
the app instance is created once at module level and reused.

Graph addresses are hardcoded constants for this cut — no catalog, no mock
mode. The workbook item id is resolved once from its SharePoint "sourcedoc"
GUID and cached at module level; the worksheet name is unknown ahead of time
so the first worksheet is resolved and cached the same way. This resolution
step is the single most likely live-integration snag (flagged by the plan) —
a 404 here is expected to need a manual live debug pass, not a CI concern.
"""

import time

import httpx
import msal
from django.conf import settings

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_DEFAULT_SCOPE = ["https://graph.microsoft.com/.default"]
SITE_HOST = "prestamosbam.sharepoint.com"
SITE_PATH = "/sites/IT"
WORKBOOK_SOURCEDOC_GUID = "a3164195-12d0-4d64-b892-549f2a705cb9"

REQUEST_TIMEOUT_SECONDS = 15

# Per-process cell cache (docs/CACHE.md layer 3 — narrow, staleness-tolerant,
# not shared across Fargate tasks). Keyed by cell address, short TTL.
CELL_CACHE_TTL_SECONDS = 60

_cache = {"site_id": None, "item_id": None, "worksheet_name": None}
_cell_cache = {}
_msal_app = None


def _authority():
    return f"https://login.microsoftonline.com/{settings.MSGRAPH_TENANT_ID}"


def _confidential_client():
    global _msal_app
    if _msal_app is None:
        _msal_app = msal.ConfidentialClientApplication(
            settings.MSGRAPH_CLIENT_ID,
            authority=_authority(),
            client_credential=settings.MSGRAPH_CLIENT_SECRET,
        )
    return _msal_app


def acquire_access_token() -> str:
    """Returns an app-only access token via client_credentials."""
    app = _confidential_client()
    result = app.acquire_token_for_client(scopes=GRAPH_DEFAULT_SCOPE)
    if "access_token" not in result:
        raise RuntimeError(
            f"msgraph_app_token_failed: {result.get('error_description', result)}"
        )
    return result["access_token"]


def _get(access_token, path):
    response = httpx.get(
        f"{GRAPH_BASE}{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def _resolve_site_id(access_token):
    if _cache["site_id"] is None:
        data = _get(access_token, f"/sites/{SITE_HOST}:{SITE_PATH}")
        _cache["site_id"] = data["id"]
    return _cache["site_id"]


def _resolve_item_id(access_token, site_id):
    if _cache["item_id"] is None:
        data = _get(access_token, f"/sites/{site_id}/drive/items/{WORKBOOK_SOURCEDOC_GUID}")
        _cache["item_id"] = data["id"]
    return _cache["item_id"]


def _resolve_worksheet_name(access_token, site_id, item_id):
    if _cache["worksheet_name"] is None:
        data = _get(
            access_token,
            f"/sites/{site_id}/drive/items/{item_id}/workbook/worksheets",
        )
        _cache["worksheet_name"] = data["value"][0]["name"]
    return _cache["worksheet_name"]


def get_cell(access_token: str, address: str) -> str:
    cached = _cell_cache.get(address)
    if cached is not None:
        value, expires_at = cached
        if time.monotonic() < expires_at:
            return value

    site_id = _resolve_site_id(access_token)
    item_id = _resolve_item_id(access_token, site_id)
    worksheet_name = _resolve_worksheet_name(access_token, site_id, item_id)
    data = _get(
        access_token,
        f"/sites/{site_id}/drive/items/{item_id}/workbook/worksheets('{worksheet_name}')"
        f"/range(address='{address}')",
    )
    value = str(data["values"][0][0])
    _cell_cache[address] = (value, time.monotonic() + CELL_CACHE_TTL_SECONDS)
    return value
