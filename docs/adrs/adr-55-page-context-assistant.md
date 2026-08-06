---
title: adr-55-page-context-assistant
type: adr
category: backend
use_case: adding or changing the page-context ask surface, editing apps/assistant/context.py or links.py, wiring AssistantDrawer, touching AssistantQuery retention
created: 2026-08-06
modified: 2026-08-06
tags: [adr, backend, assistant, chatbot, generative]
---

# ADR-55 — the page-context assistant

## CONTEXT

> One sanctioned direct channel from a user to the generating tier, read-only forever, bounded by a context the server assembles from the page's identity alone. It is a second surface inside `assistant`, never a second app.

## ASSERTIONS

1. The page-context assistant is a second surface inside the existing `assistant` app, not a new app. It adds `POST /api/assistant/ask/` beside the conversational `conversations` routes ([[adr-35-conversational-assistant]]) and takes no app name of its own, so the collision [[adr-24-feedlot-domain]] rule 2 forbids never arises and no built app is renamed.
2. This surface activates the path [[adr-15-chatbot-two-tier]] rule 9 reserves for a further generative surface, and enters through [[adr-07-development-flow]] as that rule requires. It supersedes nothing, widens no tier, and narrows none of adr-15's rules 1–8: the router keeps every actuator right and this surface holds none.
3. The assistant is read-only forever. It answers in prose and never posts a `LedgerEntry`, never mutates domain state, and never executes an action ([[adr-15-chatbot-two-tier]] rule 1, [[adr-35-conversational-assistant]] rule 1). A request for an action re-enters through the router with its closed menu (adr-15 rule 4) — a path this cut leaves out of scope and records as a seam, not a hidden debt.
4. The model's context is the requesting page's **identity only** — the current path and what the server derives from it — assembled server-side by `assemble_page_context`. Page text, DOM content, and caller-supplied context never enter the turn. A context assembled by the caller is refused, exactly as a caller-built snapshot is ([[adr-31-advisors-implementation]] rule 2).
5. Links the answer may offer come from a closed registry filtered by the requesting user's Django Groups **before** inference, via `filter_registry_links`. The model narrows within an already-authorized set and can never widen privilege; a link outside the filtered set is a hard reject logged as a fault, never repaired into a nearest match ([[adr-15-chatbot-two-tier]] rules 2–3).
6. Every turn persists an `AssistantQuery` row carrying the utterance, the page, the answer, the raw model output, the offered links, the outcome status, `model_id` and `latency_ms`. Reading a row never re-infers ([[adr-27-advisors-generative]] rule 3). Rows are retired by the `purge_assistant_audit` command; retention is an explicit act, never an implicit truncation.
7. Reaching the surface requires an authenticated session, membership decided by `CanUseAssistant` reading Django Groups per request ([[adr-10-auth]] rule 2), and the per-user opt-in `chat_drawer_enabled` ([[API]]). The opt-in is a preference and carries no authority: a user who enables it and lacks the Group reaches nothing.
8. Abuse control is the router's, reused unchanged: the per-user `CooldownThrottle` plus the silent async rate-abuse block ([[adr-30-market-prices-connectors]]-style per-source isolation does not apply here — this is the router's `rate_abuse` module). Both return `429`, indistinguishable to the caller.
9. Inference is async over Bedrock with `boto3` wrapped in `sync_to_async`, never `aiobotocore` ([[adr-16-async-mandatory]] rule 4). The real and mock clients are chosen at one selection point gated by DEBUG, the same discipline as the router and the advisors ([[adr-31-advisors-implementation]] rule 4); a non-DEBUG process can only construct the real client.
10. The surface has its own kill switch, `ASSISTANT_ENABLED` ([[VARIABLES]]), independent of `ROUTER_ENABLED`: the two tiers are disabled separately because they are permanently disjoint capabilities ([[adr-15-chatbot-two-tier]] rule 1). Disabled, the view short-circuits before any inference call, makes zero inference calls, still persists its `AssistantQuery` row, and returns a defined disabled outcome rather than an error — a switch the operator threw is not a fault. The response shape is [[API]]'s to state.
11. This is a capability layer, not a doctrine change. Cognito remains the sole authenticator ([[adr-10-auth]]), [[CACHE]] gains no cache server ([[adr-06-cache]]), every response carries an explicit `Cache-Control` and this one is `no-store`, the route enters [[API]] before code ([[adr-51-api-and-backend]] rule 1) and every variable it reads enters [[VARIABLES]] first (rule 7).

## FORBIDDEN

- **NEVER** create a second Django app for this surface (rule 1). It lives inside `assistant`, and a new app would either collide with that name or split one domain across two.
- **NEVER** put page text, DOM content, or caller-supplied context into the turn (rule 4). Path identity is the whole of what the server sends, and that is where the bound is checkable in one place.
- **NEVER** grant this surface an actuator right (rule 3). A tier that both generates prose and acts reopens the exact channel [[adr-15-chatbot-two-tier]] exists to close, permanently.
- **NEVER** filter the link registry after inference, or repair an out-of-registry link (rule 5). Authorization is decided before the model runs; a link read back from model output is a permission decision read from a model.
- **NEVER** treat `chat_drawer_enabled` as authority (rule 7). It is a preference; the Group is the grant, and a preference that gated access would be a self-service role.
- **NEVER** re-infer when reading an `AssistantQuery` (rule 6). The row is the record of what the model saw and said, and a re-run makes it a record of nothing.
- **NEVER** describe this containment as closed or proven in any document, comment, or commit message ([[adr-15-chatbot-two-tier]] rule 6). It is bounded as [[CHATBOT]] bounds it, and overstating a control is itself a defect.

## REJECTED

- **A new Django app for the page-context surface** — the template's own shape, where `assistant` is the page-context app and nothing else. It cannot be imported as-is here: this project's `assistant` app already exists as the conversational tier ([[adr-35-conversational-assistant]]), so the template's name arrives already taken. Resolved by rule 1 rather than by renaming either side, because renaming a built app is a migration, not an edit ([[adr-24-feedlot-domain]] rule 2). It would reopen only if the two surfaces grew genuinely separate domains.
- **Sending page content as the context** — the obvious reading of "page-context", and the expensive one. Rejected by rule 4: page text is user- and data-derived prose of unbounded shape, and forwarding it would make the request a free-text channel into the generating tier with no closed set anywhere in it.
- **Filtering the offered links after the model answers** — cheaper, and it reads as equivalent. Rejected by rule 5: it makes the model's output the input to an authorization decision, which is the defect [[adr-15-chatbot-two-tier]] rule 3 names outright.
- **Building the router re-entry in this cut** — the path by which the assistant would request an action against the closed menu. Explicitly out of scope (rule 3) and recorded as a seam; it enters through [[adr-07-development-flow]] with its own change.
- **Importing the template's `adr-25-page-context-assistant` file** — the direct route, and it would have been fastest. Rejected because the template's ADR numbering has forked from this project's irreconcilably (its `adr-25` is this project's `adr-35` neighbourhood, its `adr-28` is this project's [[adr-54-site-menu-lock-modes]]), and importing a numbered file would break [[adr-00-discipline]] rule 5 for every citation already pointing at those numbers here. The decision is authored fresh at this project's next free number; only the policy travelled, never the file.

## RELATED

### related adrs

- [[docs/adrs/adr-15-chatbot-two-tier]] — rules 1–6 and 9, the permanent disjunction and the path this surface enters through
- [[docs/adrs/adr-35-conversational-assistant]] — the app's first surface, which this one sits beside
- [[docs/adrs/adr-27-advisors-generative]] — rule 3, the audit-row discipline rule 6 follows
- [[docs/adrs/adr-31-advisors-implementation]] — rules 2 and 4, the refused caller-built context and the one selection point
- [[docs/adrs/adr-16-async-mandatory]] — rule 4, how Bedrock is called
- [[docs/adrs/adr-10-auth]] — rule 2, the Groups that gate this surface
- [[docs/adrs/adr-24-feedlot-domain]] — rule 2, the app-name collision rule 1 avoids
- [[docs/adrs/adr-51-api-and-backend]] — rules 1 and 7, the row before the code and the variable before the read

### related files

- [[docs/CHATBOT]] — the two tiers, the channel and the honest bound of its containment
- [[docs/API]] — the `/api/assistant/ask/` row and the `chat_drawer_enabled` contract
- [[docs/VARIABLES]] — the variables this surface reads
- [[docs/GLOSSARY]] — `AssistantQuery`, `CanUseAssistant`, `chat_drawer_enabled`, decided before first use
