---
title: adr-33-feedyard-operating-loop
type: adr
category: backend
use_case: load a pen, a ration, or a loading order, record a bunk reading, feed by pen, read the cost close by pen
created: 2026-07-25
modified: 2026-08-04
tags: [adr, feedlot, feedyard, pens, rations, bunk, phase-7]
---

# ADR-33 — The feedyard operating loop

## CONTEXT

> The daily cycle of a feedlot —diet, loading order, feed, read the bunk, adjust— lives in `feedyard`. It is the layer that plans and measures; all charging stays entirely in `feed`.

## ASSERTIONS

1. No model in `feedyard` posts a ledger entry. Feed charging belongs exclusively to `feed` via `register_feeding` ([[adr-25-account-ledger]] rule 4): `feedyard` plans (`LoadingOrder`), describes (`Ration`), and measures (`BunkScore`), and the charge appears when the ration is executed.
2. The `LoadingOrder` is the plan —what the mixer was supposed to carry to a pen for a ration— and the `FeedingEvent` is what was actually executed, with real weight and price, and the only thing that charges. They are not the same fact duplicated: their difference is the plan-vs-actual deviation, which is the management metric.
3. The `pen` on `FeedingEvent` is an additive, optional nullable FK. Feedings without a pen remain valid; the pen enriches the feeding, it is not a new condition for feeding.
4. `Ration` and `RationLine` describe the composition —which `FeedType`, at which `proportion`, with which `dry_matter_pct`— and carry no price of their own: cost appears at serving time, with the event's historical `unit_price` ([[adr-25-account-ledger]] rule 3). Dry matter lives in the recipe because technical consumption is measured in dry matter, not as-fed.
5. `Pen`, `Ration`, and `RationLine` are catalogs with full CRUD; `LoadingOrder` and `BunkScore` are dated facts: `list`/`retrieve`/`create`, no `update` or `destroy` ([[adr-24-feedlot-domain]] rule 3).
6. `register_loading_order` and `register_bunk_score` reject at the service layer —not at the view— a `Pen` with `status=inactive`, and a `LoadingOrder` rejects an inactive `Ration`. Late-entry with a backdated date is accepted as long as the pen remains active.
7. `apps.metrics` derives the cost close by pen: kilos served and feed cost in the period, read from `FeedingEvent.pen`. The gain close is completed by [[adr-42-pen-conversion-honest-cut]] over the events from [[adr-34-pen-placement]].
8. The 0–4 scale of `BunkScore` is the standard bunk-reading score. Its interpretation —raise, lower, or hold the ration— is frontend logic and is never hardcoded here as a charge or an automatic action.

## FORBIDDEN

- **NEVER** post a ledger entry from `feedyard` (rule 1). Two apps that can debit the same account for the same feed reopen the double-charge that the doctrine closed ([[adr-24-feedlot-domain]] rule 5).
- **NEVER** merge the loading order with the feeding (rule 2). The plan-vs-actual deviation is lost, which is the metric that tells whether the bunk is being read correctly.
- **NEVER** make `pen` mandatory on a `FeedingEvent` (rule 3). That would be rewriting the stable domain to accommodate new information.
- **NEVER** assign a price to a `Ration` (rule 4). Editing the recipe would rewrite historical cost.
- **NEVER** derive a pen conversion without knowing which livestock was there (rule 7). That would be a fabricated number, which is what [[adr-29-metrics-derivation]] rule 2 forbids.

## REJECTED

- **Charging from the loading order** — debiting what was planned instead of what was served. Rejected by rule 1: it would charge kilos the mixer may not have delivered, and would open a second charging path over the same account.
- **A single entity for plan and execution** — the order that is marked as fulfilled and becomes the feeding. Rejected by rule 2; the deviation ceases to exist the moment the two facts are one.
- **The gain close in this phase** — pen conversion alongside cost. Deferred for metric honesty and later resolved by [[adr-42-pen-conversion-honest-cut]] once `PenPlacement` provided the missing attribution.

## RELATED

### related adrs

- [[docs/adrs/adr-25-account-ledger]] — rule 4, the only feed charging path
- [[docs/adrs/adr-24-feedlot-domain]] — growth by addition and event immutability
- [[docs/adrs/adr-34-pen-placement]] — where the livestock is, the missing piece
- [[docs/adrs/adr-42-pen-conversion-honest-cut]] — the gain half of the pen close
- [[docs/adrs/adr-29-metrics-derivation]] — the contract for numbers that are not fabricated

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `Pen`, `Ration`, `RationLine`, `LoadingOrder`, `BunkScore`
- [[docs/FEEDLOT]] — the daily loop in operation
- [[docs/API]] — the `feedyard` routes
