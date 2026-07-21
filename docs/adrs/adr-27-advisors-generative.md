---
title: adr-27-advisors-generative
type: adr
status: proposed
created: 2026-07-21
tags: [adr, feedlot, advisors, ai]
---

# ADR-27 — advisors are a generative capability, bounded

Rules only; content lives in [[FEEDLOT]] (advisors section) and [[FEEDLOT-DATA-MODEL]].

1. The three advisors — `livestock`, `finance`, `admin` — are a GENERATIVE capability:
   they produce free analytical text over a client's metrics. This is a named exception to
   the router's zero-generation posture ([[adr-15-chatbot-two-tier]]): the exception is
   bounded to the `advisors` app and its endpoints and widens nothing about the router,
   which stays a closed-enum chooser. Advisors and the router share no code path.
2. An advisor is READ-ONLY over data. It reasons only over an `input_snapshot` assembled by
   the backend for one client and one period; it does not query the database itself, does not
   read another client's data, and executes no action or mutation. A per-client scope is a
   hard boundary, not a convention.
3. Every run is persisted as an `AdvisorReport` with its `input_snapshot`, `output`,
   `model_id`, `tokens` and `latency` — reproducible and auditable. The report is the record;
   the generation is not repeated on read.
4. Generation is inference and follows the inference rules already in force: async
   ([[adr-16-async-mandatory]]), on AWS Bedrock, cost- and rate-bounded, gated by a DRF
   permission and RBAC group ([[adr-10-auth]]) — reports are generated on demand or on a
   schedule, never on every data write.
5. The advisor endpoints are declared in [[API]] before code
   ([[adr-03-api-and-backend]]); the advisor role prompts are configuration on the `Advisor`
   catalog rows, English-keyed ([[LOCALIZATION]]), with Spanish only in rendered output.
