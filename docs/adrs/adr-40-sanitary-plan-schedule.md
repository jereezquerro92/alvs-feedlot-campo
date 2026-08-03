---
title: adr-40-sanitary-plan-schedule
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, sanitary, vaccination, plan, schedule, phase-13]
---

# ADR-40 — the sanitary plan and the vaccination schedule

**Context:** grows by addition on top of `sanitary`
([[adr-49-domain-layer-and-growth-by-addition]] rule 1), reuses the animal/lot XOR constraint
of [[adr-26-livestock-individual-and-lot]] and the event-sourced posture of
[[adr-49-domain-layer-and-growth-by-addition]] rule 3. Extends
[[adr-28-animal-lifecycle-and-sanitary]] without touching the charging that ADR fixed. Rules
only; the entities live in [[FEEDLOT-DATA-MODEL]].

## Context

Phase 2 left the `HealthEvent`: a one-off application that already happened and that is always
charged ([[adr-28-animal-lifecycle-and-sanitary]] decision 5). What is missing is the other
thing every feedlot manages: the **sanitary plan** — the schedule of which vaccine/treatment is
due and when, against which what is **pending** is controlled. A plan is future intent; a
`HealthEvent` is a past fact. They are distinct things and are not collapsed. The sanitary
planning layer is added to the `sanitary` app, without touching how charging works.

## Decisions

### 1. The plan is a reusable editable template; the enrollment is an immutable event

`SanitaryPlan` + `SanitaryPlanItem` are master data: a ModelViewSet with full CRUD — "loading a
plan" is creating the plan and its doses. `PlanEnrollment` (enrolling an animal or lot in a
plan with a start date) is a dated fact: list/retrieve/create, without update or destroy
([[adr-49-domain-layer-and-growth-by-addition]] rule 3).

*Why:* a plan has composition that gets corrected (a dose is added, a day is adjusted); an
enrollment is a fact — "this lot was started on this plan on this day" — that is not rewritten.
The same idiom as `Ration`/`LoadingOrder` (adr-33): the recipe is edited, the execution is
immutable.

### 2. The schedule is relative; the due date is derived, never stored

Each `SanitaryPlanItem` fixes a `HealthProduct` and a `day_offset` (days from the enrollment's
`start_date`). A dose's due date is **derived** (`start_date + day_offset`) per enrollment; no
absolute date is stored in the plan. That way one plan serves many targets, each with its own
start date.

*Why:* a vaccination schedule is "N days after entering"; storing absolute dates in the
template would tie it to a single animal. The relative offset makes the plan reusable, which is
the whole point of a template.

### 3. Each dose's status is derived by crossing the schedule with the `HealthEvent`s

`applied` / `pending` / `upcoming` is not persisted anywhere. It is derived: a dose is
**applied** when a `HealthEvent` exists for the same target and the same product with a date ≥
`start_date`; otherwise it is **pending** when its due date has already passed (`due_date ≤
as_of`) and **upcoming** when it has not. With no enrollments, the schedule is an empty list —
never a filler zero nor an invented status (the posture of [[adr-29-metrics-derivation]] rule
2).

*Why:* the pending set is a claim about the herd's real sanitary state, and it has to come out
of the facts (the `HealthEvent`s), not out of an editable flag someone forgets to tick.
Deriving it guarantees that the schedule and what was actually applied cannot contradict each
other — they are the same source.

### 4. Neither the plan nor the enrollment touches the ledger

No model in this phase posts an entry. Sanitary charging remains exclusively the
`HealthEvent`'s via `register_health_event` ([[adr-28-animal-lifecycle-and-sanitary]] decision
5, [[adr-25-account-ledger]]). A plan is intent; an enrollment is a schedule commitment;
neither is an input delivered. The charge appears only when the dose is actually applied, and
that is a `HealthEvent`.

*Why:* a single charging path. Charging on enrollment would charge a vaccine that may never be
applied, and would reopen the door to the double charge the doctrine closed (a fact is stated
once, adr-49 rule 5).

### 5. The enrollment validates in the service, not in the view

`enroll_in_plan` rejects, in the **service**, an inactive plan, a target that does not belong
to the client, a non-active target (dead/sold/departed is not enrolled) and the absence of the
exact animal/lot XOR. Late entry with a retroactive date is accepted while the target is still
active — the same field norm as adr-28.

*Why:* business rules live in the service, the single write point, so that view, admin and
command share the same validation.

### 6. One single target per enrollment, at the database level

A `PlanEnrollment` points to an `Animal` OR a `Lot`, never both and never neither — a `CHECK`
constraint with two nullable FKs, identical to the one on lifecycle events
([[adr-26-livestock-individual-and-lot]] rule 3, [[adr-28-animal-lifecycle-and-sanitary]]
decision 1).

*Why:* reusing the already-proven shape avoids a polymorphic table and keeps the query direct.

## Consequences

- The backend enters only through [[API]] ([[adr-03-api-and-backend]]) and is born through the
  [[TDD]] flow ([[adr-07-development-flow]]); this ADR grants no exception to that path.
- The migrations are three new tables in `sanitary` (`SanitaryPlan`, `SanitaryPlanItem`,
  `PlanEnrollment`); nothing outside the app, nothing in `ledger`.
- The derived schedule is a read-only `GET` (the `schedule` action of the enrollments viewset);
  it is computed on read, never materialized as an editable field
  ([[adr-49-domain-layer-and-growth-by-addition]] rule 3).
- No environment variables are added: it is internal data, with no external services.
- `HealthEvent` is not refactored: the "applied" status is derived by looking at the existing
  events; no field and no FK is added to `HealthEvent` (the extraction looks forward,
  [[adr-32-multi-rubro-assets]] rule 2).
- No sanitary stock is kept in this phase (adr-28 decision 6 stands): the plan schedules
  applications, not holdings.
- Any change to rules 1–6 is semantic and MUST supersede this ADR
  ([[adr-00-adr-doctrine]] rule 4).
