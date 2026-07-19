---
title: tdd-03-router-bedrock-inference
type: tdd
status: green
created: 2026-07-18
api: ["POST /api/router/route/"]
tags: [tdd, router, bedrock, chatui]
---

# tdd-03 — router Bedrock inference and the blocking connectivity gate

## Context

Closes #253. The router's choosing tier ([[CHATBOT]], [[adr-15-chatbot-two-tier]]) shipped wired to `MockInferenceClient` — a deterministic echo, so "behind the login we always have AI" was an appearance, not a property. This entry wires the real Bedrock call behind the existing [[API]] row `POST /api/router/route/` (no new route, no new variable — `BEDROCK_REGION` and `ROUTER_BEDROCK_MODEL_ID` already have their [[VARIABLES]] rows) and adds the blocking connectivity gate the issue requires. Feeds [[bdd-04-chatui-router]] (backend half).

## Design

- **`BedrockInferenceClient`** (`backend/apps/router/inference.py`): synchronous `boto3` `bedrock-runtime` `converse` on `ROUTER_BEDROCK_MODEL_ID` in `BEDROCK_REGION`, temperature 0 ([[adr-15-chatbot-two-tier]] rule 7). Callers on the event loop wrap it in `asgiref.sync_to_async`, never `aiobotocore` ([[adr-16-async-mandatory]] rule 4). `boto3` is imported lazily in the constructor so the mock path stays import-free. The client returns the model's raw text; menu-membership enforcement (the hard reject) stays in the view — an empty/malformed response maps to `""`, which is never a menu member, so it always rejects.
- **`get_inference_client()`** — the one selection point. `DEBUG=True` → mock; otherwise the real client, unconditionally. This is the [[adr-10-auth]] rule 6 precedent applied to inference (**decision 2**, mock coexistence): the mock is a DEBUG-only development path no setting can force into a deploy context.
- **Gate scoping (decision 1)**: the blocking gate runs (a) from a developer terminal as `manage.py check_bedrock_connectivity` and (b) as the `bedrock_live`-marked pytest wrapping that same command, executed by a dedicated `bedrock-gate` job in `deploy-prod.yml` with OIDC credentials, blocking the deploy before any image is built. It does **not** run at prod container boot.
- **Probe cost (decision 3)**: the gate makes the cheapest real call that still proves model access and IAM — one `converse` with `maxTokens=1` on Nova Micro (sub-cent per run, one call per deploy). Reachability-only checks (`list_foundation_models`) were rejected: they pass with a missing model grant, the documented failure mode ([[CHATBOT]] AccessDenied triage).
- **Outage behavior (decision 4)**: a Bedrock failure at request time (`BotoCoreError`/`ClientError`) degrades the router surface only — `503 {"detail": "router_unavailable"}` with its `IntentQuery` audit row (`choice="unavailable"`), the `ROUTER_ENABLED=False` shape. The backend never crashes and the choice is never defaulted or retried ([[adr-15-chatbot-two-tier]] rule 2).
- Constrained decoding: Nova Micro on `converse` exposes no server-side enum constraint, so closure is enforced code-side (menu-membership hard reject), exactly the fallback [[adr-15-chatbot-two-tier]] rule 7 sanctions.
- Response outcomes stay closed: valid enum member → the existing `Action`/`NO_MATCH`/`Escalate` payloads; anything else → `422 router_hard_reject`; inference failure → `503 router_unavailable`. All responses stay `Cache-Control: no-store` ([[adr-06-cache]] rule 4).

## Tests (`backend/apps/router/`)

- `test_inference.py` — factory gating (mock only under `DEBUG`); `converse` request shape (temperature 0, model ID, full menu + utterance in the prompt); raw off-menu text returned unrepaired; malformed/empty responses map to `""`; transport errors propagate.
- `test_route_view.py::test_inference_failure_degrades_to_503_with_audit_row` — decision 4 as a routed-view test.
- `test_bedrock_gate.py` — the `bedrock_live`-marked gate: `check_bedrock_connectivity` hard-fails on any unreachability; excluded from the default suite like `cognito_live`, run explicitly by the deploy pipeline.
- Existing `test_route_view.py` / `test_route_utterance.py` pin the deterministic mock explicitly (they test the route contract, not Bedrock).

## Status

`draft → red → green` in one batch (#253): the new tests were written against the mock-only module (red: no `BedrockInferenceClient`, no factory, no 503 path, no gate command) and turned green by the implementation above. `done` when the gate has passed in a real `deploy-prod` run.
