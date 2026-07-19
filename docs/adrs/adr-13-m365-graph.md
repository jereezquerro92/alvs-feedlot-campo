---
title: adr-13-m365-graph
type: adr
status: active
created: 2026-07-12
tags: [adr, m365, graph, backend]
---

# ADR-13 — Microsoft Graph app-only capability

Rules only; content lives in [[API]], [[VARIABLES]].

1. Microsoft Graph is a capability layer, not a second login IdP, and is app-only. Cognito remains the sole authentication provider ([[adr-10-auth]]); the `m365` app authenticates to Graph via OAuth2 `client_credentials` (owner override, supersedes the delegated-only design) — zero human interaction, no user tokens, no browser flow.
2. No token is ever stored. The app has no models. An access token is minted per request via `msal.ConfidentialClientApplication.acquire_token_for_client` and discarded; refresh-at-rest rules are moot under this mode.
3. Named exception, bounded to two routes: `GET /api/m365/hello/` and `GET /api/m365/world/` are deliberately `AllowAny`, no session required — an explicit owner-directed scope reduction for demo purposes. This does not widen RBAC doctrine ([[adr-10-auth]]) anywhere else; every other route in this app follows normal auth.
4. No mock mode, no resource catalog, no KMS in this cut. Graph addresses (site host, site path, workbook item, worksheet) are hardcoded Python constants in `graph.py`; YAGNI supersedes any catalog/mock design for this build.
5. Graph REST v1.0 only. No beta endpoints.
6. `MSGRAPH_RESOURCE_CATALOG` is out of scope for code in this cut — omitted from [[VARIABLES]] because doctrine requires a row only for a variable actually read ([[adr-03-api-and-backend]] rule 7). Same for `MSGRAPH_SCOPES` and `MSGRAPH_TOKEN_FERNET_KEY`: app-only mode reads neither (the `.default` scope is a hardcoded constant), so both are dropped from settings and [[VARIABLES]].
