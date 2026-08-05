---
title: adr-31-advisors-implementation
type: adr
category: backend
use_case: generate an advisor report, build or change the snapshot, choose the inference client, test generation without network
created: 2026-07-23
modified: 2026-08-04
tags: [adr, feedlot, advisors, inference, bedrock, phase-5]
---

# ADR-31 — Advisors implementation

## CONTEXT

> How the advisors that [[adr-27-advisors-generative]] established were built. The delicate piece is not generation — asking a model for text is easy — but ensuring that text is auditable and scoped to a single client.

## ASSERTIONS

1. `apps.advisors.snapshot.build_snapshot` is the only point that touches a client's database. The advisor receives a dict and nothing more: inside there is no path to the database or to another client ([[adr-27-advisors-generative]] rule 2).
2. `generate_report` builds the snapshot with the `client` it receives and does not accept one built externally, so a caller cannot smuggle in data from another client. The per-client scope is a hard barrier, not a convention.
3. The snapshot is built from `apps.metrics` ([[adr-29-metrics-derivation]]): the advisor and the chart the client sees read the same numbers and cannot contradict each other. If conversion comes out "not calculable" on the dashboard, it comes out the same way for the advisor.
4. `AdvisorBedrockClient` (real) and `MockAdvisorClient` (deterministic) are chosen in `get_advisor_client`, the sole selection point, gated by DEBUG just like the router ([[adr-15-chatbot-two-tier]]). A non-DEBUG process can only build the real client; no setting forces the mock into a deploy. Unlike the router, this tier generates prose: temperature 0.3.
5. Every generation persists an `AdvisorReport` with snapshot, output, `model_id`, tokens, and latency; reading a report does not re-infer ([[adr-27-advisors-generative]] rule 3). That is what makes an economic suggestion auditable: you can see exactly what data the model saw.
6. Real inference requires `ADVISOR_BEDROCK_MODEL_ID` and the region in [[VARIABLES]], the IAM permission, the Bedrock connectivity gate, and the async wrapper from [[adr-16-async-mandatory]] rule 4 (`sync_to_async`, never `aiobotocore`). Tests run against the mock.
7. Generation is on-demand or scheduled: the `POST` triggers one and no signal generates on its own. Viewsets expose `list`/`retrieve`/`create` for reports and never a mutation of client data. An inactive advisor rejects generation in the service, not in the view.

## FORBIDDEN

- **NEVER** accept a snapshot built by the caller (rule 2). That is the path by which another client's data enters the package without anything noticing.
- **NEVER** give the advisor a path to the database (rule 1). The snapshot is everything it sees, and that is why the barrier is verified in a single place.
- **NEVER** select the inference client outside `get_advisor_client` (rule 4). Two selection points are two policies, and one of them forgets the gate.
- **NEVER** allow a setting to force the mock outside DEBUG (rule 4). A deploy that responds with deterministic text appears to work.
- **NEVER** re-infer when reading a report (rule 5). The record would cease to be the record.
- **NEVER** use `aiobotocore` for inference (rule 6). [[adr-16-async-mandatory]] rule 4 mandates `boto3` wrapped in `sync_to_async`.

## REJECTED

- **Receiving the snapshot as an endpoint parameter** — letting the caller build the package and the service only infer. Rejected by rule 2: it would make client isolation a caller convention.
- **Defining snapshot metrics inside `advisors`** — the advisor's own formulas, adjusted for what it needs to narrate. Rejected by rule 3; the advisor and the dashboard must only be able to contradict each other if the facts change.
- **Temperature 0 as in the router** — the same configuration as the choosing tier. Not applicable: this tier generates prose, and it is the bounded generative exception of [[adr-27-advisors-generative]].

## RELATED

### related adrs

- [[docs/adrs/adr-27-advisors-generative]] — the rules this ADR implements
- [[docs/adrs/adr-29-metrics-derivation]] — the single definition of each number in the snapshot
- [[docs/adrs/adr-15-chatbot-two-tier]] — the inference client pattern that rule 4 mirrors
- [[docs/adrs/adr-16-async-mandatory]] — rule 4, how Bedrock is called
- [[docs/adrs/adr-35-conversational-assistant]] — the same pattern, in the assistant

### related files

- [[docs/VARIABLES]] — `ADVISOR_BEDROCK_MODEL_ID` and the region
- [[docs/FEEDLOT-DATA-MODEL]] — `Advisor` and `AdvisorReport`
- [[docs/API]] — the advisor routes
