---
title: adr-16-async-mandatory
type: adr
category: backend
use_case: writing a streaming or long-running view, reaching for WebSockets, calling Bedrock, choosing sync or async for a new view
created: 2026-07-14
modified: 2026-08-02
tags: [adr, async, backend, sse, streaming]
---

# ADR-16 — async as a carried capability

## CONTEXT

> The project is always able to go async. That is a property of the server and the dependencies, not an instruction for each view.

## ASSERTIONS

1. The project stays async-capable at all times: the ASGI server, the config and the dependencies never block a view from being `async def`. This is a capacity requirement, not a per-view mandate — a sync `def` view is the unchanged default and needs no justification.
2. A feature that streams, does non-blocking I/O or waits on long-running inference is written `async def`. Server-Sent Events — an async view returning `StreamingHttpResponse` over an async generator — is the sanctioned streaming mechanism, riding the existing ASGI server ([[BACKEND]]). No Django Channels, no channel layer, no new infrastructure.
3. WebSockets are a reserved escalation at the `/ws/` prefix, for a need SSE genuinely cannot meet, and only in a shape needing no cross-process channel layer. Channels' production layer is Redis-backed and Redis is prohibited ([[adr-06-cache]] rule 1), so a design requiring fan-out across Fargate tasks is not buildable in this stack.
4. Bedrock inference calls use `boto3` wrapped in `asgiref.sync_to_async` ([[BACKEND]], [[REQUIREMENTS]]) — the one concrete requirement this capability imposes today.

## FORBIDDEN

- **NEVER** add Django Channels or a channel layer to reach async (rule 2). SSE over the existing ASGI server is the mechanism, and the layer Channels needs is the one thing this stack refuses.
- **NEVER** use `aiobotocore` for a Bedrock call (rule 4). One AWS SDK, wrapped where it must be awaited.
- **NEVER** rewrite a working sync view as `async def` for its own sake (rule 1). The capability exists for features that need it.

## REJECTED

- **Async as the default for every new view** — the posture this ADR held until 2026-08-02, on the reasoning that results should reach the browser as they arrive. It lost as a blanket default because most views do no I/O worth awaiting, and an `async def` around blocking work is slower and harder to read than the sync view it replaced. What survived is rule 1's capacity requirement plus rule 2's trigger. It would reopen if the majority of views became streaming ones.
- **`aiobotocore`** — the native-async AWS client, which would remove the thread-pool wrap of rule 4. Rejected as a second, less mainstream AWS SDK to carry for one call path; it reopens only on measured evidence that `sync_to_async` is a real bottleneck.

## RELATED

### related adrs

- [[docs/adrs/adr-06-cache]] — rule 1, the Redis prohibition that closes the WebSocket fan-out shape
- [[docs/adrs/adr-15-chatbot-two-tier]] — the inference path rule 4 governs

### related files

- [[docs/BACKEND]] — the ASGI server, the SSE mechanics and the sync/async posture
- [[docs/constitution/REQUIREMENTS]] — the `boto3` pin
