---
title: adr-28-animal-lifecycle-and-sanitary
type: adr
category: backend
use_case: register a weighing, a death or an exit, load a sanitary application, calculate ADG for a lot, touch the sanitary app
created: 2026-07-21
modified: 2026-08-04
tags: [adr, feedlot, livestock, sanitary, lifecycle, phase-2]
---

# ADR-28 — Animal lifecycle and the `sanitary` app

## CONTEXT

> What happened to the animal after it entered and ate: how much it gained, whether it died, when it left, and what sanitary care it received. The three lifecycle events share shape but not table, and sanitary care is always charged.

## ASSERTIONS

1. `Weighing`, `Death`, and `Exit` inherit from the abstract `LifecycleEvent`, which contributes the `animal`/`lot` pair and its XOR constraint ([[adr-26-livestock-individual-and-lot]] rule 3). Each one keeps its own table.
2. The ADG of a lot is compared per head (`total_weight / head_count`). If `head_count` differs between the two weighings, the period is reported with `adg = null` and `not_calculable = "head_count_changed"`: a lot's total shifts due to entries, deaths, and exits, not only by weight gain.
3. A death does not create a ledger entry — the feed and sanitary care already consumed remain charged and a death does not reverse them. An exit does not reverse them either, and in its `transfer`/`other` types it posts nothing. The sale-exit (`Exit.kind=sale`) does settle, per [[adr-43-sale-settlement]]: client livestock (`kind=boarding`) pays a fattening commission as a service debit; own livestock (`kind=own`) records the proceeds as a credit in the own account. `sale_price_per_kg` is the price that settlement captures ([[adr-25-account-ledger]] rule 3).
4. The sanitary domain app is named `sanitary`, because `apps.health` is the template's liveness probe and the probe is a contract with the orchestrator.
5. Every sanitary application is charged: `register_health_event` always posts a debit. There is no equivalent to the feed's `origin=client_stock`, because sanitary products are always supplied by the feedlot.
6. Lifecycle events are immutable: viewsets expose `list`/`retrieve`/`create`, without `update` or `destroy`. A dead or sold animal rejects subsequent weighings and sanitary applications; late entry with a retroactive date is accepted as long as the target is still active.

## FORBIDDEN

- **NEVER** calculate a lot's ADG on the total weight (rule 2). The total is moved by the herd entering and leaving, so the number would measure anything but growth.
- **NEVER** fill a non-calculable ADG with an estimate (rule 2). A plausible and false number graphs the same as a real one ([[adr-29-metrics-derivation]] rule 2).
- **NEVER** automatically reverse charges for a death (rule 3). That would turn the feedlot into the client's insurer, which is a business decision; if taken, it enters as an explicit and auditable `adjustment`.
- **NEVER** rename `apps.health` to free up the name (rule 4). The probe is a contract with the orchestrator; what gets renamed is the new domain.
- **NEVER** expose `update` or `destroy` on a lifecycle event (rule 6). A correction is another event.

## REJECTED

- **A single table of polymorphic events** — `Weighing`, `Death`, and `Exit` in one table with a type field. Rejected because of the nullable fields it forces on every row and the type filter on every query; the abstract shares the constraint without merging the domains.
- **A `origin=client_stock` for sanitary care** — the sanitary equivalent of client-supplied feed. Rejected as speculative complexity: today the feedlot always supplies the products. Reopens when a client brings their own vaccine, adding the field then.
- **Tracking sanitary stock in this phase** — inventory on top of applications, replicating `FeedStockMovement`. Not taken: the volume is low and the real problem with vaccines is expiry and the cold chain, not the balance. The pattern remains available for when that problem is truly solved; [[adr-40-sanitary-plan-schedule]] added the schedule without touching this.
- **The sale as a client fact, with no economic footprint** — the policy this ADR held until [[adr-43-sale-settlement]]: `sale_price_per_kg` was informational and no exit posted anything. Replaced by rule 3 with the owner's consent; deaths continue to leave the ledger untouched.

## RELATED

### related adrs

- [[docs/adrs/adr-26-livestock-individual-and-lot]] — rule 3, the XOR the abstract contributes
- [[docs/adrs/adr-25-account-ledger]] — what the ledger charges and what it does not
- [[docs/adrs/adr-43-sale-settlement]] — the settlement of rule 3
- [[docs/adrs/adr-29-metrics-derivation]] — the "not calculable" contract of rule 2
- [[docs/adrs/adr-40-sanitary-plan-schedule]] — the sanitary plan over these events

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `LifecycleEvent`, `Weighing`, `Death`, `Exit`, `HealthEvent`
- [[docs/FEEDLOT]] — the animal lifecycle in the operation
- [[docs/API]] — the lifecycle and sanitary routes
