---
title: adr-27-advisors-generative
type: adr
category: backend
use_case: adding or changing an advisor, building an input snapshot, generating or reading a report, wiring inference for the advisors app
created: 2026-07-21
modified: 2026-08-02
tags: [adr, feedlot, advisors, ai]
---

# ADR-27 — advisors are a generative capability, bounded

## CONTEXT

> The advisors write prose about one client's numbers. They are the named generative exception to the router's zero-generation posture, read-only over data, and every run leaves a record of exactly what the model saw.

## ASSERTIONS

1. The three advisors — `livestock`, `finance` and `admin` — produce free analytical text over a client's metrics. The exception is bounded to the `advisors` app and its endpoints; the router stays a closed-enum chooser ([[adr-15-chatbot-two-tier]]) and the two share no code path.
2. An advisor is read-only over data. It reasons only over an `input_snapshot` the backend assembles for one client and one period; it does not query the database, does not read another client's data, and executes nothing. The per-client scope is a hard boundary.
3. Every run persists an `AdvisorReport` carrying its `input_snapshot`, `output`, `model_id`, `tokens` and `latency`. The report is the record — reading one never re-runs the generation.
4. Generation follows the inference rules already in force: async ([[adr-16-async-mandatory]]), on Bedrock, cost- and rate-bounded, gated by a DRF permission and an RBAC group ([[adr-10-auth]]). Reports are generated on demand or on a schedule, never on a data write.
5. The advisor endpoints are declared in [[API]] before code ([[adr-03-api-and-backend]]). The role prompts are configuration on the `Advisor` catalog rows, English-keyed ([[LOCALIZATION]]), with Spanish only in rendered output.

## FORBIDDEN

- **NEVER** give an advisor a path to the database (rule 2). The snapshot is the whole of what it sees, which is what makes the per-client boundary checkable in one place.
- **NEVER** accept a snapshot assembled by the caller (rule 2). Built outside the service, it can carry another client's numbers ([[adr-31-advisors-implementation]] rule 2).
- **NEVER** let an advisor execute an action or a mutation (rules 1–2). The tier that generates does not act; that boundary is permanent ([[adr-15-chatbot-two-tier]] rule 1).
- **NEVER** re-infer on a read (rule 3). The stored report is the record, and a re-run would answer a question nobody asked again, differently.
- **NEVER** trigger generation from a data write (rule 4). Inference costs money per call and a write path can fire in a loop.

## REJECTED

- **Letting the advisor query the data itself** — tools or an ORM handle inside the generation. Rejected because the per-client boundary would then be enforced at every query the model chooses to make instead of at one snapshot the backend builds.
- **Generating on every data write** — a report refreshed as the operation records facts. Rejected on cost and noise: reports are read occasionally and written constantly, and rule 4 puts the trigger where the reading is.
- **Folding the advisors into the router** — one app doing both choosing and generating. Rejected outright; it is the exact merge [[adr-15-chatbot-two-tier]] rule 1 exists to prevent.

## RELATED

### related adrs

- [[docs/adrs/adr-15-chatbot-two-tier]] — the router this is the bounded exception to
- [[docs/adrs/adr-31-advisors-implementation]] — how the snapshot, the clients and the reports are built
- [[docs/adrs/adr-29-metrics-derivation]] — the single definition of every number in the snapshot
- [[docs/adrs/adr-16-async-mandatory]] — rule 4, how inference is called
- [[docs/adrs/adr-10-auth]] — the permission and group that gate generation

### related files

- [[docs/FEEDLOT]] — the advisors section
- [[docs/FEEDLOT-DATA-MODEL]] — `Advisor` and `AdvisorReport`
- [[docs/API]] — the advisor endpoints
