---
title: adr-31-advisors-implementation
type: adr
status: active
created: 2026-07-23
tags: [adr, feedlot, advisors, ai, implementation, phase-5]
---

# ADR-31 — the advisors implementation

**Context:** implements [[adr-27-advisors-generative]]; reuses the pattern of [[adr-15-chatbot-two-tier]] (inference clients) and respects [[adr-16-async-mandatory]].

## Context

ADR-27 fixed the advisors' rules; this is how they were built. The delicate piece is not
the generation — asking a model for text is easy — but guaranteeing that the text is
**auditable and bounded to one client**.

## Decisions

### 1. The snapshot is the only thing that reads data

`apps.advisors.snapshot.build_snapshot` is the single point that touches a client's
database. The advisor receives a dict and nothing else. Inside the advisor there is no
path to the database nor to another client (adr-27 rule 2).

### 2. The snapshot is assembled in the service, not received

`generate_report` builds the snapshot with the `client` it is given; it does not accept a
snapshot assembled from outside. That way a caller cannot slip another client's data into
the package. Per-client scope is a hard barrier, not a convention.

### 3. One single definition of each metric

The snapshot is assembled from `apps.metrics` (Phase 3). The advisor and the chart the
client sees read the same numbers — they cannot contradict each other because they are the
same source. If conversion comes out "not calculable" on the dashboard, it comes out the
same for the advisor.

### 4. An inference client traced from the router

`AdvisorBedrockClient` (real) and `MockAdvisorClient` (deterministic) with
`get_advisor_client` as the single selection point, gated by DEBUG exactly as the router
is (adr-15). A non-DEBUG process can only build the real client; no setting forces the
mock into a deploy. The difference from the router: this tier **generates prose**
(temperature 0.3, not 0) — it is adr-27's bounded generative exception.

### 5. The report is the record

Every generation persists an `AdvisorReport` with its snapshot, output, model_id, tokens
and latency. Reading a report does **not** re-run inference (adr-27 rule 3). This is what
makes an economic suggestion auditable: one can see exactly what data the model saw.

## Pending integration point (Claude Code, against AWS)

`AdvisorBedrockClient` follows the router's pattern but needs, against real AWS: the
`ADVISOR_BEDROCK_MODEL_ID` and the region in `VARIABLES`, the IAM permission, the Bedrock
connectivity gate (like the router's `bedrock_live`), and the async wrapper (adr-16 rule 4:
`sync_to_async`, never `aiobotocore`). The tests run against `MockAdvisorClient`, just as
the router tests its tier with its own mock.

## Consequences

- Generation is on demand or scheduled, never on every data write (adr-27 rule 4). The
  POST endpoint triggers one; there is no signal that generates on its own.
- The advisor is read-only: the viewsets expose list/retrieve/create of reports, never a
  mutation of the client's data.
- An inactive advisor rejects the generation in the service, not in the view.
