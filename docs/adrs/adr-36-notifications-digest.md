---
title: adr-36-notifications-digest
type: adr
category: backend
use_case: build or change the weekly digest, add a delivery channel, send a notification, test sending without credentials
created: 2026-07-25
modified: 2026-08-04
tags: [adr, feedlot, notifications, digest, whatsapp, phase-9]
---

# ADR-36 — Notifications: the digest and the delivery channel

## CONTEXT

> Pushing a summary to the client without them having to log in: head count, balance, and conversion, via WhatsApp. `notifications` builds the text from the metrics and sends it; it calculates nothing of its own and does not operate on the domain.

## ASSERTIONS

1. `build_weekly_digest` reads `apps.metrics.services.summary` for a client and renders it to text. It defines no new metrics: the digest number is the same as on the dashboard and the advisor ([[adr-29-metrics-derivation]] rule 1).
2. `get_sender(channel)` is the sole selection point: in DEBUG it returns `MockSender` —no network, records what was sent— and outside DEBUG the real channel sender. No setting forces the mock in a deploy, same gate as the inference clients; tests run against the mock.
3. `Notification` stores `client`, `channel`, `to_address`, `subject`, `body`, and a `status` ∈ {`pending`, `sent`, `failed`} with its `error` and `sent_at`. It is created and read, no `update` or `destroy` ([[adr-24-feedlot-domain]] rule 3): a retry is a new notification.
4. `notifications` is read-only over client data: reads metrics, builds text, and sends. It posts no ledger entry and changes no domain state — it is an output layer, not an actuator.
5. `WHATSAPP_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` are registered in [[VARIABLES]] before being read ([[adr-51-api-and-backend]] rule 7) and are only read by the real sender. They live in local `.env` or in Secrets Manager, never in git.
6. The `send_weekly_digests` command builds and sends per client, and a send failure for one client does not stop the others — same isolation discipline as `ingest_prices` ([[adr-30-market-prices-connectors]] rule 7).

## FORBIDDEN

- **NEVER** recalculate a metric inside the digest (rule 1). The client would read a different number in the message than what they see on screen.
- **NEVER** select the sender outside `get_sender` (rule 2). Two selection points are two policies and one of them forgets the gate.
- **NEVER** let a setting force the mock outside DEBUG (rule 2). A deploy that "sends" without actually sending appears healthy.
- **NEVER** overwrite the status of a notification (rule 3). The attempt history would be lost, which is precisely what needs to be audited.
- **NEVER** post a ledger entry from `notifications` (rule 4). Informing is not operating; charging still belongs to the ledger via `feed`.

## REJECTED

- **Retrying by editing the failed notification** — an attempt counter on the same row. Rejected by rule 3: the record of what was sent and with what result is lost the moment it is overwritten.
- **A global `try/except` in the command** — a single catch for the whole batch. Rejected by rule 6: a failure for one client would stop or silence the others.

## RELATED

### related adrs

- [[docs/adrs/adr-29-metrics-derivation]] — the sole definition of each number in the digest
- [[docs/adrs/adr-31-advisors-implementation]] — rule 4, the mock/real gate by DEBUG
- [[docs/adrs/adr-30-market-prices-connectors]] — rule 7, per-item isolation in the command
- [[docs/adrs/adr-24-feedlot-domain]] — rule 3, the immutable record

### related files

- [[docs/VARIABLES]] — `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`
- [[docs/FEEDLOT-DATA-MODEL]] — `Notification`
- [[docs/API]] — the notification routes
