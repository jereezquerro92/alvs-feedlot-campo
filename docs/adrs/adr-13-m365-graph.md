---
title: adr-13-m365-graph
type: adr
category: backend
use_case: calling Microsoft Graph, minting a Graph token, adding an m365 route, adding an MSGRAPH_ variable
created: 2026-07-12
modified: 2026-08-02
tags: [adr, m365, graph, backend]
---

# ADR-13 — Microsoft Graph app-only capability

## CONTEXT

> Graph is a capability the backend calls as itself. It is not a second way to log in, and it stores nothing.

## ASSERTIONS

1. Microsoft Graph is a capability layer, app-only. Cognito remains the sole authentication provider ([[adr-10-auth]] rule 1); the `m365` app authenticates to Graph via OAuth2 `client_credentials` — no human interaction, no user tokens, no browser flow.
2. No token is stored and the app has no models. An access token is minted per request via `msal.ConfidentialClientApplication.acquire_token_for_client` and discarded.
3. Two routes are exempt from the session requirement: `GET /api/m365/hello/` and `GET /api/m365/world/` are `AllowAny`, for demonstration. Every other route in the app follows normal auth, and this exemption widens RBAC doctrine nowhere else ([[adr-10-auth]] rule 2).
4. Graph addresses — site host, site path, workbook item, worksheet — are Python constants in `graph.py`. There is no resource catalog, no mock mode and no KMS in this app.
5. Graph REST v1.0 only. No beta endpoints.
6. The variables this app reads are exactly the three in [[VARIABLES]] ([[adr-03-api-and-backend]] rule 7). App-only mode reads no scope variable — the `.default` scope is a constant — and no token key, because rule 2 stores nothing.

## FORBIDDEN

- **NEVER** treat Graph as a login path (rule 1). A user identity arrives from Cognito only; Graph answers as the application.
- **NEVER** persist or cache a Graph token (rule 2). It is minted per request and discarded, which is what makes refresh-at-rest a question this app never has to answer.
- **NEVER** extend the `AllowAny` pair to a third route (rule 3). Two demonstration routes are the whole exemption.
- **NEVER** call a Graph beta endpoint (rule 5).
- **NEVER** add an `MSGRAPH_` variable that no code reads (rule 6, [[adr-03-api-and-backend]] rule 7). A declared-but-unread variable is a phantom that outlives whoever added it.

## REJECTED

- **Delegated (per-user) Graph access** — the original design: a user consents, the app holds their token and acts on their behalf. Retired by owner override in favour of app-only, because the app's Graph work is background work with no user in the loop, and a stored user token is a credential at rest that rule 2 now never creates. It would reopen only for a feature that must act as the signed-in user.
- **A resource catalog and a mock mode** (`MSGRAPH_RESOURCE_CATALOG`, a fake Graph) — planned, then dropped as speculative for a cut whose Graph addresses are four constants (rule 4). Both reopen when a second Graph target appears, not before.

## RELATED

### related adrs

- [[docs/adrs/adr-10-auth]] — rules 1 and 2, the authentication and RBAC doctrine this capability does not touch
- [[docs/adrs/adr-03-api-and-backend]] — rule 1 for the route rows, rule 7 for the variables

### related files

- [[docs/API]] — the `m365` rows, including the two `AllowAny` ones
- [[docs/VARIABLES]] — the three `MSGRAPH_` variables and where their values live
