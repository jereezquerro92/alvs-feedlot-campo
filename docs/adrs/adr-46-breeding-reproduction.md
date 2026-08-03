---
title: adr-46-breeding-reproduction
type: adr
status: active
created: 2026-07-28
tags: [adr, feedlot, breeding, livestock, reproduction, event-sourced, phase-breeding]
---

# ADR-46 — cow-calf and backgrounding: the reproductive events (`breeding`)

**Context:** grows by addition on top of the spine
([[adr-49-domain-layer-and-growth-by-addition]] rule 1): a new `breeding` app, without touching
`livestock` or the ledger beyond the single charge the owner defined. Reuses the animal/lot XOR
constraint of [[adr-26-livestock-individual-and-lot]] and the `LifecycleEvent` abstract of
[[adr-28-animal-lifecycle-and-sanitary]] decision 1; the template→relative-schedule idiom of
[[adr-40-sanitary-plan-schedule]] for the FTAI protocol; the "not calculable" contract of
[[adr-29-metrics-derivation]] for the metrics; and the generic `(source_kind, source_id)` pair of
[[adr-49-domain-layer-and-growth-by-addition]] rule 4 for the single entry. Depends on
[[adr-47-genetics-semen-embryo]] for bulls, semen and embryos. Rules only; the entities live in
[[FEEDLOT-DATA-MODEL]], the names in [[GLOSSARY]] (`GLOSSARY-feedlot-additions.md`) before their
first use ([[adr-01-glossary-and-localization]]).

## Context

Up to today the system knows the animal entering, eating, gaining, falling ill and leaving, but
it does not know it **reproducing**. What is missing is the heart of a cow-calf herd: the cycle
`service → pregnancy check → calving → weaning`, from which come the metrics that justify the
business line (pregnancy %, calving %, weaning %, calving interval, kg weaned per dam).
Backgrounding — growing the weaned calf to a target weight — is **already almost entirely done**:
it reuses `Weighing`/ADG, `feed`, `sanitary` and pen placement. What is genuinely new is
reproduction. The `breeding` app is added with those four facts, without rewriting the stable
domain.

## Decisions

### 1. `breeding` is immutable reproductive events; almost nothing touches the ledger

`breeding` has no business catalogs of its own beyond the FTAI protocol (decision 5): it is four
dated events. None posts an entry **except** the AI service charge on client cattle (decision 6).
Charging for feed and sanitary work stays exclusively in `feed` and `sanitary`
([[adr-25-account-ledger]], [[adr-28-animal-lifecycle-and-sanitary]]).

*Why:* a single charging path. Reproduction is above all a management record; the only economic
fact the owner defined is the invoiced insemination service.

### 2. Four events, each targeting `Animal` XOR `Lot`, at the database level

`Service`, `PregnancyCheck`, `Calving` and `Weaning` inherit from `LifecycleEvent`
([[adr-28-animal-lifecycle-and-sanitary]] decision 1): the `animal`/`lot` pair with a `CHECK` for
exactly one ([[adr-26-livestock-individual-and-lot]] rule 3). Each keeps its own table and
exposes `list`/`retrieve`/`create`, without `update` or `destroy`
([[adr-49-domain-layer-and-growth-by-addition]] rule 3). An individual service is on one cow;
systematic FTAI is loaded on a `Lot` (a herd served together).

*Why:* reusing the already-proven shape avoids a polymorphic table and keeps the query direct.
All four need identically "exactly one target".

### 3. Reproductive status is DERIVED from the events, never stored

`open` / `served` / `pregnant` / `calved` / `dry` is not an editable field on `Animal` nor
anywhere else: it is derived by crossing each dam's `Service`, `PregnancyCheck` and `Calving`
([[adr-49-domain-layer-and-growth-by-addition]] rule 3). The pregnancy diagnosis in force is the
latest `PregnancyCheck`; the pregnancy is closed by the corresponding `Calving`.

*Why:* a mutable reproductive flag drifts out of sync with the facts. Deriving it guarantees
that the status and the events cannot contradict each other — they are the same source.

### 4. The calving creates the calf; the pedigree is derived, without touching `Animal`

A `Calving` with result `live` on an individual cow **creates** an `Animal` (`category=calf`)
and references it in `Calving.calf` (nullable FK). The dam is the calving's target
(`Calving.animal`), the sire is the bull of the service that confirmed the pregnancy
(`Calving.service → Service.sire`, [[adr-47-genetics-semen-embryo]]). The pedigree is **derived**
from that chain; **no** `dam`/`sire` field is added to `Animal` — the extraction looks forward
([[adr-32-multi-rubro-assets]] rule 2, [[adr-38-senasa-traceability]]'s ear tag precedent). A
`Calving` on a `Lot` records `births_count` and adds head to the calf lot, without creating
per-head identity ([[adr-26-livestock-individual-and-lot]] rule 1).

*Why:* `Intake` already creates `Animal`s, so an event that begets an animal has precedent.
Deriving the pedigree instead of denormalizing it onto `Animal` keeps `livestock` stable and
makes the parentage auditable from the fact that produced it.

### 5. The FTAI protocol is an editable template with a relative schedule

`IatfProtocol` + `IatfProtocolStep` are master data: a ModelViewSet with full CRUD — "loading a
protocol" is creating the protocol and its steps (day 0 device, day 7 prostaglandin, etc.). Each
step fixes a relative `day_offset`; each step's absolute date is **derived** from the
`Service.date` of the insemination that references the protocol, and is never stored in the
template. The same idiom as `SanitaryPlan`/`SanitaryPlanItem` ([[adr-40-sanitary-plan-schedule]]
decisions 1–2).

*Why:* a protocol is "N days after starting"; storing absolute dates would tie it to a single
service. The relative offset makes it reusable, which is the point of a template.

### 6. Only AI/FTAI on client cattle charges; the rest posts nothing

A `Service` with `method ∈ {ai, iatf}` on cattle of a `Client(kind=boarding)` posts **one
`debit` with `concept=service`** to the client's account, for the insemination fee, via the
generic pair `(source_kind="breeding_service", source_id=<Service.id>)`
([[adr-49-domain-layer-and-growth-by-addition]] rule 4). It snapshots the day's `service_price`
(the fee) ([[adr-25-account-ledger]] rule 3). A `natural` service, a service on own cattle, and
the `PregnancyCheck`, `Calving` and `Weaning` events post **no** entry. The cost of the semen
consumed is handled by `genetics` as a stock `out`, not as a charge here
([[adr-47-genetics-semen-embryo]] decision 6).

*Why:* the owner defined exactly one economic fact in reproduction — AI invoiced to the boarding
client — and no other. Modelling a charge per pregnancy check or per calving that is not
invoiced today is speculative complexity (the same criterion as
[[adr-28-animal-lifecycle-and-sanitary]] decision 5); if the pregnancy check gets charged
tomorrow, it enters through the same seam with its own change.

### 7. The service consumes genetics and validates in the service, not in the view

`register_service` draws down a `SemenMovement` `out` from the `SemenBatch` for `method ∈ {ai,
iatf}`, and an `EmbryoMovement` `out` from the `EmbryoBatch` for `method=embryo_transfer`
([[adr-47-genetics-semen-embryo]]). It rejects, in the **service**: a non-active target
(dead/sold/departed is not served), a target belonging to another client, the absence of the
exact XOR, a `SemenBatch`/`EmbryoBatch` with no stock or inactive, and an inactive
`IatfProtocol`. Late entry with a retroactive date is accepted while the target is still active —
the same field norm as [[adr-28-animal-lifecycle-and-sanitary]].

*Why:* business rules live in the service, the single write point, so that view, admin and
command share the same validation.

### 8. Reproductive metrics are derived in `apps.metrics`, honest about the gap

`apps.metrics` gains, as pure functions over the events ([[adr-29-metrics-derivation]] rule 1):
`pregnancy_rate` (pregnancy % = pregnant/served), `calving_rate` (calving % =
calved/pregnant), `weaning_rate` (weaning % = weaned/calved), `calving_interval` (average days
between calvings per dam) and `kg_weaned_per_dam`. Each returns `null` with its
`not_calculable` (`no_services_in_period`, `no_pregnancy_checks`, `no_calvings`, …) when the
input is missing, never a filler zero ([[adr-29-metrics-derivation]] rule 2).

*Why:* a "pregnancy % = 0" and a "there were no services to evaluate" are opposite situations;
the zero conflates them, the explicit gap distinguishes them and tells the operator what to
measure.

### 9. Backgrounding gains no app: it reuses what exists plus a `Weaning` with a purpose

The weaned calf remains a normal `Animal`: its backgrounding is measured with `Weighing`/ADG,
fed with `feed`, treated with `sanitary` and placed with `PenPlacement` — nothing new. The only
backgrounding addition is the `Weaning` (weaning weight and date) with a `purpose`
(`replacement` | `sale` | `undecided`) marking the selection of replacement heifers.

*Why:* backgrounding is the fattening of an already-modelled animal; creating a parallel app
would duplicate `livestock`/`feed` without adding a new fact. Weaning was the only milestone
missing.

## Consequences

- The backend enters only through [[API]] ([[adr-03-api-and-backend]]) and is born through the
  [[TDD]] flow ([[adr-07-development-flow]]); this ADR grants no exception to that path
  ([[adr-49-domain-layer-and-growth-by-addition]] rule 6).
- Migrations: the new tables live in `breeding` (`Service`, `PregnancyCheck`, `Calving`,
  `Weaning`, `IatfProtocol`, `IatfProtocolStep`) and a nullable `calf` FK from `Calving` to
  `livestock.Animal`. Nothing outside the new app; nothing in `ledger` (the AI debit reuses
  `Concept.SERVICE` through the seam, with no new model and no new concept).
- The `advisors`/`assistant` apps gain these metrics without changing their code: they read
  `apps.metrics` ([[adr-29-metrics-derivation]] rule 1, [[adr-31-advisors-implementation]]
  decision 3).
- `ASSISTANT`/`ADVISOR` and the other variables do not change: `breeding` adds no credentials and
  no external services.
- The RBAC gating of these routes is declared in [[API]] with its permission class before the
  code ([[adr-44-field-operational-roles]] decision 7): reproductive data entry belongs to
  `field_managers` (and `feed_operators` where applicable), reading follows the role's rules.
- Any change to rules 1–9 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
