---
title: adr-35-conversational-assistant
type: adr
category: backend
use_case: ask in natural language about a client, add a turn or a conversation, touch the assistant's snapshot or inference client
created: 2026-07-25
modified: 2026-08-04
tags: [adr, feedlot, assistant, generative, chatbot, phase-8]
---

# ADR-35 — The conversational assistant is the bounded generating tier

## CONTEXT

> Querying a client's data in natural language, multi-turn, and receiving a grounded response. `assistant` is the generating tier of [[adr-15-chatbot-two-tier]]: free prose, read-only forever, permanently disjoint from the router that chooses.

## ASSERTIONS

1. The assistant produces analytical prose about a client's data and never executes an action, posts a ledger entry, or changes domain state. It is the generating tier of [[adr-15-chatbot-two-tier]] rule 1: read-only, forever. Triggering an action would mean re-entering through the router with its closed menu (rule 4 of that ADR), a path this phase leaves out of scope.
2. Each turn reasons only over an `input_snapshot` that the backend builds for a client ([[adr-27-advisors-generative]] rule 2). The assistant does not query the database, does not read another client, and does not execute anything; the snapshot is built in the service from the conversation's `client` and is not received pre-built from outside ([[adr-31-advisors-implementation]] rule 2).
3. The snapshot is built with `apps.advisors.snapshot.build_snapshot`, which reads `apps.metrics`. The assistant, the advisor, and the chart the client sees all read the same numbers and cannot contradict each other. If the conversion comes out as "not calculable" on the dashboard, it comes out the same here.
4. A `Conversation` is a thread per client and each `Message` of role `assistant` persists its `input_snapshot`, `model_id`, `tokens`, and `latency_ms`. Reading a message does not re-infer: it shows exactly what data the model saw in each response.
5. `AssistantBedrockClient` (real, `converse`, temperature 0.3) and `MockAssistantClient` (deterministic, no network) are selected in `get_assistant_client`, the sole selection point, gated by DEBUG exactly like the router and advisors. A non-DEBUG process can only construct the real client; tests run against the mock.
6. Conversations and messages expose `list`/`retrieve`/`create`, no `update` or `destroy` ([[adr-24-feedlot-domain]] rule 3): a turn is a dated fact and a correction is another turn.
7. Inference follows the rules in force: async with `sync_to_async` over `boto3` ([[adr-16-async-mandatory]] rule 4), over Bedrock. `ASSISTANT_BEDROCK_MODEL_ID` is registered in [[VARIABLES]] before being read ([[adr-51-api-and-backend]] rule 7) and reuses `BEDROCK_REGION`.
8. This is a capability layer, not a doctrine change: Cognito remains the sole authenticator ([[adr-10-auth]]), [[CACHE]] gains no server ([[adr-06-cache]]), and the router remains the sole holder of actuator rights.

## FORBIDDEN

- **NEVER** grant the assistant actuator rights (rule 1). A tier that both generates prose and executes actions reopens exactly the channel that [[adr-15-chatbot-two-tier]] exists to close.
- **NEVER** accept a snapshot pre-built from outside (rule 2). That is the path by which another client's data would enter the turn.
- **NEVER** give the assistant a path to the database (rule 2). The snapshot is all it sees, and that is where the barrier is verified.
- **NEVER** re-infer when reading a message (rule 4). The record would no longer say what the model saw when it responded.
- **NEVER** edit or delete a turn (rule 6). A correction is another turn.

## REJECTED

- **A single tier that chooses and generates** — an assistant with access to the router's action menu. Rejected outright: it is the merge that [[adr-15-chatbot-two-tier]] rule 1 declares permanently forbidden.
- **Building the router re-entry in this phase** — the path by which the assistant would request an action with the menu closed. Explicitly out of scope; recorded as a seam, not a hidden debt.
- **Defining assistant-specific metrics** — numbers calculated for the conversation. Rejected by rule 3: the assistant and the dashboard must read the same source.

## RELATED

### related adrs

- [[docs/adrs/adr-15-chatbot-two-tier]] — the permanent disjunction between choosing and generating
- [[docs/adrs/adr-27-advisors-generative]] — the bounded generative precedent and per-client scope
- [[docs/adrs/adr-31-advisors-implementation]] — the snapshot and inference client this replicates
- [[docs/adrs/adr-45-lot-owner-assistant-access]] — who can reach these routes and with what scope
- [[docs/adrs/adr-16-async-mandatory]] — rule 4, how Bedrock is called

### related files

- [[docs/CHATBOT]] — the two tiers and the boundary between them
- [[docs/VARIABLES]] — `ASSISTANT_BEDROCK_MODEL_ID` and `BEDROCK_REGION`
- [[docs/API]] — the conversations and messages routes
