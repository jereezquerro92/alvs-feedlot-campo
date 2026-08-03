---
title: adr-35-conversational-assistant
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, assistant, generative, chatbot, phase-8]
---

# ADR-35 — the conversational assistant is the generating tier, bounded

**Context:** activates the generating-tier seam that [[adr-15-chatbot-two-tier]] rule 9 left
open; reuses the bounded generative precedent of [[adr-27-advisors-generative]] and the
inference pattern of [[adr-31-advisors-implementation]].

## Context

The router (the router phase) is the tier that **chooses**: closed enum, zero generation,
holding actuator rights. The advisors (Phase 5) are one-shot **report** generation per role.
What is missing is the surface every competitor has: **asking the client's data in natural
language** and getting a grounded answer — multi-turn, not a closed report. That is the
`assistant` app.

`assistant` is the tier that **generates** of [[adr-15-chatbot-two-tier]]: it produces free
text and is **read-only forever**. It is not a relaxation of the router; it is the other
half, permanently disjoint (adr-15 rule 1).

## Decisions

### 1. The assistant generates text and NEVER acts

`assistant` produces analytical prose about a client's data and never executes an action,
never posts an entry, never changes domain state. It is the generating tier of adr-15 rule
1: read-only, forever. If one day it wants to trigger an action, it **re-enters through the
router** with its closed menu (adr-15 rule 4) — a path this phase does not build and
explicitly leaves out of scope.

*Why:* the boundary between choosing and generating is a permanent invariant of adr-15, not
a transitional arrangement. A tier that generates prose and also acts reopens exactly the
channel that ADR exists to close.

### 2. Per-client scope is a hard barrier, traced from the advisors

Every assistant turn reasons **only** over an `input_snapshot` the backend assembles for ONE
client (adr-27 rule 2). The assistant does not query the database, does not read another
client, executes nothing. The snapshot is built in the service with the conversation's
`client`; it is not received pre-assembled from outside (adr-31 rule 2).

### 3. One single definition of each metric

The snapshot is assembled with `apps.advisors.snapshot.build_snapshot`, which reads
`apps.metrics` (Phase 3). The assistant, the advisor and the chart the client sees read the
same numbers — they cannot contradict each other because they are the same source (adr-31
rule 3). If conversion comes out "not calculable" on the dashboard, it comes out the same for
the assistant.

### 4. Every assistant turn is an auditable record

A `Conversation` is a thread per client; every `Message` with role `assistant` persists its
`input_snapshot`, `model_id`, `tokens` and `latency_ms`. Reading a message does **not**
re-run inference (adr-27 rule 3). One can see exactly what data the model saw in each answer.

### 5. An inference client traced from the router and the advisors

`AssistantBedrockClient` (real, `converse`, temperature 0.3 — it generates prose) and
`MockAssistantClient` (deterministic, no network) with `get_assistant_client` as the single
selection point, gated by DEBUG exactly as the router (adr-15) and the advisors (adr-31 rule
4) are. A non-DEBUG process can only build the real client; no setting forces the mock into a
deploy. The tests run against the mock.

### 6. Editable catalog, immutable events

A `Conversation` is created and listed; `Message`s are created and read —
list/retrieve/create, without update or destroy (adr-49 rule 3). A turn is a dated fact: a
correction is another turn, not editing the past.

## Consequences

- The backend enters only through [[API]] (adr-03) and is born through the [[TDD]] flow
  (adr-07).
- Inference follows the rules in force: async ([[adr-16-async-mandatory]] rule 4,
  `sync_to_async` over `boto3`, never `aiobotocore`), on Bedrock, gated by DEBUG.
  `ASSISTANT_BEDROCK_MODEL_ID` enters [[VARIABLES]] before it is read
  ([[adr-03-api-and-backend]] rule 7); it reuses `BEDROCK_REGION`.
- This is a capability layer, not a doctrine change (the adr-13/adr-27 precedent): Cognito
  remains the sole authenticator ([[adr-10-auth]]); [[CACHE]] gains no cache server
  ([[adr-06-cache]]); the router remains the only holder of actuator rights.
- Any change to rules 1–5 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
