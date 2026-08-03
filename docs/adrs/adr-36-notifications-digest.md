---
title: adr-36-notifications-digest
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, notifications, digest, whatsapp, phase-9]
---

# ADR-36 — notifications: the digest and the delivery channel

**Context:** reuses the metrics of [[adr-29-metrics-derivation]] (one single definition of
each number) and the DEBUG-gated mock/real client pattern of
[[adr-31-advisors-implementation]] and [[adr-35-conversational-assistant]].

## Context

Every competitor pushes summaries to the client without the client having to come and look:
a weekly WhatsApp digest with head, balance and conversion. What is missing is the layer that
**assembles a summary and sends it over a channel**. That is the `notifications` app.

## Decisions

### 1. The digest is assembled from the metrics, not recomputed

`build_weekly_digest` reads `apps.metrics.services.summary` for ONE client and renders it to
text. It defines no new metric: the number the client sees in the digest is the same one on
the dashboard and in the advisor (adr-29 rule 1, adr-31 rule 3).

*Why:* three consumers with three definitions of "conversion" is exactly what the metrics
doctrine exists to prevent.

### 2. Delivery is an abstraction with mock and real, gated by DEBUG

`get_sender(channel)` is the single selection point: in DEBUG it returns `MockSender` (no
network, records what was sent); outside DEBUG it returns the channel's real sender
(`WhatsAppSender`). No setting forces the mock into a deploy — the same gate as the inference
clients (adr-31 rule 4, adr-35 decision 5). The tests run against the mock.

*Why:* external delivery depends on live credentials that exist neither in test nor in dev;
the mock keeps the logic testable and the real one stays pluggable without touching the flow.

### 3. A notification is an immutable record with its status

`Notification` stores `client`, `channel`, `to_address`, `subject`, `body`, and a `status` ∈
{`pending`, `sent`, `failed`} with its `error` and `sent_at`. It is created and read —
list/retrieve/create, without update or destroy (adr-49 rule 3). A retry is a new
notification, not an edit of the previous one.

*Why:* the record of what was sent, to whom and with what result has to be auditable;
overwriting the status would lose the history of attempts.

### 4. Notifying touches neither the ledger nor the domain

`notifications` is read-only over the client's data: it reads metrics, assembles text, sends.
It posts no entry, changes no domain state. It is an output layer, not an actuator (the same
posture as `feedyard`/adr-33 with respect to charging).

*Why:* sending a summary is informing, not operating. A single charging path remains the
ledger via `feed` (adr-25).

## Consequences

- The backend enters only through [[API]] (adr-03) and is born through the [[TDD]] flow
  (adr-07).
- `WHATSAPP_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` enter [[VARIABLES]] before they are read
  ([[adr-03-api-and-backend]] rule 7); only `WhatsAppSender` reads them, never the mock. They
  are not secrets in git — they live in local `.env` or Secrets Manager.
- The `send_weekly_digests` command assembles and sends per client; a delivery failure for
  one client does not stop the others (the same isolation discipline as `ingest_prices`).
- Any change to rules 1–4 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
