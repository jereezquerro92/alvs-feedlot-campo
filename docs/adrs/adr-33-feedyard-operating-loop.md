---
title: adr-33-feedyard-operating-loop
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, feedyard, pens, rations, bunk, phase-7]
---

# ADR-33 — the pen operating loop (`feedyard`)

**Context:** extends [[adr-49-domain-layer-and-growth-by-addition]] ("grows by addition") and
[[adr-25-account-ledger]] (charging belongs to the ledger, and to nobody else). It is born
from evaluating a competitor's feedlot software (Cattler): the daily loop diet → loading
order → feed → read the bunk → adjust is the heart of a feedlot and today we lack it. Rules
only; the entities live in [[FEEDLOT-DATA-MODEL]].

## Context

Up to Phase 6 the system knew *what* an animal or lot ate (`FeedingEvent`) and *how much* it
cost, but it did not know the physical **pen**, the diet's **recipe**, nor the planning and
control cycle a feedlot runs every day. Without a pen there is no per-pen close; without a
recipe there is no dry matter; without a bunk reading there is no ration adjustment. A
`feedyard` app is added, supplying that **operational and monitoring** layer, without
touching how charging works.

## Decisions

### 1. `feedyard` is planning and monitoring; it does NOT charge

No `feedyard` model posts an entry. Charging for feed remains exclusively `feed`'s, via
`register_feeding` (adr-25 rule 4). `feedyard` plans (`LoadingOrder`), describes (`Ration`)
and measures (`BunkScore`); the charge is made by `feed` when the ration is executed.

*Why:* a single charging path. Two apps able to debit the same account for the same feed
reopen the door to the double charge doctrine closed (a fact is stated once, adr-49 rule 5).

### 2. The loading order is the PLAN; the `FeedingEvent` is what was EXECUTED

`LoadingOrder` records what the mixer **was supposed** to deliver to a pen for a ration
(planned as-fed kg). `FeedingEvent` (extended with an optional `pen`) remains what was
**actually** served, with real weight and price, and is the only thing that charges. They
are not the same fact duplicated: they are plan and execution, and their difference is
precisely the management figure (was more or less loaded than planned?).

*Why:* Cattler and any serious feedlot distinguish the loading order from the mixer's real
weighing. Merging them loses the plan-vs-actual deviation, which is the metric that says
whether the bunk is being read well.

### 3. The `pen` on `FeedingEvent` is additive and optional

A nullable `pen` FK is added to `feed.FeedingEvent`. Existing feedings and per-animal/lot
ones without a pen stay valid; nothing becomes mandatory.

*Why:* the stable domain is not rewritten (the same criterion as adr-32 rule 2). The pen is
information that enriches the feeding, not a new condition for being able to feed.

### 4. The ration is a recipe, not a costed item

`Ration` + `RationLine` describe the **composition** (which `FeedType`, in what
`proportion`, with what `dry_matter_pct`). The ration has no price of its own: the cost
appears only when it is served, with the `FeedingEvent`'s historical `unit_price`
(adr-25 rule 3). Dry matter lives in the recipe because technical consumption is measured in
dry matter, not as-fed.

*Why:* separating the formula (stable, editable) from the price (historical, per event)
keeps editing a recipe from rewriting the past. The `FeedType` is an input; the `Ration` is
how inputs are combined — they are different things and are not collapsed.

### 5. Catalogs are edited; events are immutable

`Pen`, `Ration` and `RationLine` are master data: full CRUD. `LoadingOrder` and `BunkScore`
are dated facts: list/retrieve/create, without update or destroy (adr-49 rule 3). A
correction to an event is another event.

*Why:* the same event-sourced posture as the rest of the system. A pen is corrected (it is
deactivated, it is renamed); yesterday's bunk reading is not rewritten.

### 6. An inactive pen and an inactive ration reject new events

`register_loading_order` and `register_bunk_score` reject a `Pen` with `status=inactive` in
the **service** (not in the view); a `LoadingOrder` rejects an inactive `Ration`. Late entry
with a retroactive date is accepted while the pen is still active (the same criterion as
adr-28 for animals).

### 7. The per-pen close, in this phase, is on the cost side

`apps.metrics` gains a per-pen summary: kilos served and feed cost per pen in the period,
read from `FeedingEvent.pen`. The close by **gain** (kg produced and conversion per pen)
needs animal/lot → pen placement with movements, and is explicitly deferred to Phase 7b
along with the pen map.

*Why:* a close by gain without knowing which animals were in the pen and how much they
weighed would be an invented number — exactly what adr-29 forbids. What can be stated
honestly is delivered (the cost) and what cannot is deferred.

## Consequences

- The backend enters only through [[API]] (adr-03) and is born through the [[TDD]] flow
  (adr-07); this ADR grants no exception to that path (adr-49 rule 6).
- `feedyard` gains no migrations that touch `ledger`; the only migration outside the new app
  is the additive `pen` FK in `feed`.
- The 0–4 scale of `BunkScore` is the standard bunk-reading scale; its interpretation
  (raise/lower/hold the ration) is Phase 7b/frontend logic, and is not hardcoded here as a
  charge nor as an automatic action.
- Any change to rules 1–5 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
