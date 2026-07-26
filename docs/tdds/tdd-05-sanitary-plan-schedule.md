---
title: tdd-05-sanitary-plan-schedule
type: tdd
status: green
created: 2026-07-25
api: [
  "/api/sanitary-plans/",
  "/api/sanitary-plan-items/",
  "/api/plan-enrollments/",
  "/api/plan-enrollments/schedule/",
]
tags: [tdd, feedlot, sanitary, vaccination, plan, schedule, phase-13]
---

# tdd-05 — El plan sanitario y el calendario derivado

## Context

Closes issue #18 and implements [[adr-40-sanitary-plan-schedule]]. The `sanitary`
app had only the point-in-time `HealthEvent` ([[adr-28-animal-lifecycle-and-sanitary]]);
it had no way to record a **plan** — what to apply and when — nor to answer "what is
pending?". This entry adds the plan template, the immutable enrollment, and the derived
calendar. The API rows above were declared in [[API]] before this code
([[adr-03-api-and-backend]] rule 2).

## Design

Three models in `apps.sanitary` ([[BACKEND]], [[FEEDLOT-DATA-MODEL]]):

- `SanitaryPlan` (catalog): `name`, `description`, `is_active`. Reusable template.
- `SanitaryPlanItem` (catalog line): `plan` FK (`related_name=items`), `product`
  → `HealthProduct`, `day_offset` (days after enrollment start), `dose`, `notes`.
  Ordered by `day_offset`.
- `PlanEnrollment` (immutable event): `plan`, `client`, `animal` XOR `lot`
  (DB `CHECK` constraint, same shape as `HealthEvent` / the lifecycle events,
  [[adr-26-livestock-individual-and-lot]] rule 3), `start_date`, `notes`, `created_by`.

The write path is a service, `enroll_in_plan`, exactly like `register_health_event`:
it validates the XOR, an active plan, target-belongs-to-client and an active target,
then creates the row. It posts **no** ledger entry — billing stays with `HealthEvent`
([[adr-40-sanitary-plan-schedule]] decision 4, [[adr-25-account-ledger]]).

The calendar is a pure derivation, `plan_schedule_for_client(client, as_of=…)`: for each
of the client's enrollments whose target is still active, for each plan item, it computes
`due_date = start_date + day_offset` and marks the dose `applied` when a `HealthEvent`
exists for the same target and product dated `>= start_date`, else `pending` when
`due_date <= as_of`, else `upcoming`. Nothing is stored; no enrollments → empty list
(no filled zero, [[adr-29-metrics-derivation]] posture). It is exposed as the
`schedule` detail-action (`GET`) on `PlanEnrollmentViewSet`. Catalog CRUD is a plain
`ModelViewSet`; the enrollment viewset is `list`/`retrieve`/`create` only
([[adr-24-feedlot-domain]] rule 3). No new [[VARIABLES]]; no cache layer added
([[CACHE]], `no-store`).

## Tests (`backend/apps/sanitary/test_sanitary_plan.py`)

1. `test_enroll_in_plan_creates_immutable_event_and_posts_no_ledger` — enrolling an
   active animal in an active plan creates a `PlanEnrollment` and writes **zero**
   `LedgerEntry` rows (decision 4).
2. `test_enroll_requires_exactly_one_target` — neither/both of animal+lot raises.
3. `test_enroll_rejects_foreign_target` — a target of another client raises.
4. `test_enroll_rejects_inactive_target` — a dead animal cannot be enrolled.
5. `test_enroll_rejects_inactive_plan` — an `is_active=False` plan raises.
6. `test_schedule_marks_due_dose_pending_and_future_dose_upcoming` — with two items
   (offset 0 and 30) and `as_of` between them, the first is `pending`, the second
   `upcoming`.
7. `test_schedule_marks_applied_when_matching_health_event_exists` — a `HealthEvent`
   for the same target+product at/after start flips that dose to `applied`.
8. `test_schedule_empty_for_client_without_enrollments` — a client with no enrollment
   returns an empty item list and `pending_count == 0`, never a fabricated state.

## Status

`draft → red → green`. Written test-first against the real routed views and the real
database (no mocks). Red with the models/service/views absent; green once the migration,
`enroll_in_plan`, `plan_schedule_for_client`, and the three viewsets landed. Record the
green run in the PR that closes #18.
