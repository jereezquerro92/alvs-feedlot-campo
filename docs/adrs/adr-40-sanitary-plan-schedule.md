---
title: adr-40-sanitary-plan-schedule
type: adr
category: backend
use_case: load a sanitary plan or its doses, enrol an animal or lot, read which vaccine is pending, touch the derived schedule
created: 2026-07-25
modified: 2026-08-04
tags: [adr, feedlot, sanitary, vaccination, plan, schedule, phase-13]
---

# ADR-40 — The Sanitary Plan and Vaccination Schedule

## CONTEXT

> The plan is future intention —which vaccine is due and when— and the `HealthEvent` is a past fact. They are distinct things and are not collapsed: the plan schedules, the event applies and charges, and the pending status comes from crossing the two.

## ASSERTIONS

1. `SanitaryPlan` and `SanitaryPlanItem` are editable catalogues with full CRUD: "loading a plan" means creating the plan and its doses. `PlanEnrollment` —enrolling an animal or lot with a start date— is a dated fact: `list`/`retrieve`/`create`, no `update` or `destroy` ([[adr-24-feedlot-domain]] rule 3). Same idiom as `Ration`/`LoadingOrder`: the recipe is edited, the execution is immutable.
2. Each `SanitaryPlanItem` sets a `HealthProduct` and a `day_offset` in days from the enrolment's `start_date`. The due date is derived per enrolment and is never stored as an absolute date in the template, which is what makes the plan reusable.
3. The status of each dose is derived and not persisted: it is **applied** when a `HealthEvent` of the same target and product with date ≥ `start_date` exists; otherwise it is **pending** when its due date has passed and **upcoming** when it has not. Without enrolments the schedule is an empty list, never a fabricated state ([[adr-29-metrics-derivation]] rule 2).
4. No model in this phase posts a ledger entry. The sanitary charge continues to come exclusively from `HealthEvent` via `register_health_event` ([[adr-28-animal-lifecycle-and-sanitary]] rule 5): a plan is intention and an enrolment is a schedule commitment, and the charge appears when the dose is actually applied.
5. `enroll_in_plan` rejects in the service —not in the view— an inactive plan, a target that does not belong to the client, a non-active target, and the absence of the exact XOR. Late loading with a retroactive date is accepted as long as the target remains active.
6. A `PlanEnrollment` points to an `Animal` or to a `Lot`, never both and never neither: `CHECK` with two nullable FKs, identical to the one for lifecycle events ([[adr-26-livestock-individual-and-lot]] rule 3).
7. The derived schedule is a read-only `GET` —the `schedule` action on the enrolment viewset— computed at read time. `HealthEvent` is not refactored: the "applied" status is derived by inspecting existing events, without adding a field or FK to it ([[adr-32-multi-rubro-assets]] rule 2). No sanitary stock is tracked in this phase.

## FORBIDDEN

- **NEVER** persist `applied`, `pending`, or `upcoming` as a flag (rule 3). The pending status is a statement about the herd's actual sanitary condition and comes from the facts, not a checkbox someone forgets to tick.
- **NEVER** store absolute dates in the template (rule 2). It would tie the plan to a single animal and it would cease to be a template.
- **NEVER** charge on enrolment (rule 4). It would charge for a vaccine that may never be applied and would reopen the double-charge issue the doctrine closed.
- **NEVER** edit an enrolment (rule 1). It is the fact that that lot was started on that plan on that day.
- **NEVER** validate the enrolment in the view (rule 5). The rule lives in the service, which view, admin, and command all share.

## REJECTED

- **Collapsing the plan and the `HealthEvent`** — a single model that serves as both scheduling and application, with a field indicating whether it has occurred. Rejected because it mixes intention and fact: the event is charged and the plan is not, and the flag would replace the derivation of rule 3.
- **An `applied` flag on the dose** — marking the dose as applied when loading the event. Rejected against rule 3: the schedule and what was actually applied could contradict each other, which is exactly what deriving prevents.
- **Sanitary stock in this phase** — inventory on top of the schedule. Still not tracked, for the same reason as in [[adr-28-animal-lifecycle-and-sanitary]]: the real problem with vaccines is expiry and the cold chain, not the balance.

## RELATED

### related adrs

- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — the `HealthEvent` that charges and against which the pending status is derived
- [[docs/adrs/adr-24-feedlot-domain]] — rules 1 and 3, addition and immutable event
- [[docs/adrs/adr-26-livestock-individual-and-lot]] — rule 3, the enrolment XOR
- [[docs/adrs/adr-33-feedyard-operating-loop]] — the editable template / immutable execution precedent
- [[docs/adrs/adr-29-metrics-derivation]] — rule 2, never a filler state

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `SanitaryPlan`, `SanitaryPlanItem`, `PlanEnrollment`
- [[docs/API]] — the plan, enrolment, and schedule routes
