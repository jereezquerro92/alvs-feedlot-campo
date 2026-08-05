---
title: adr-46-breeding-reproduction
type: adr
category: backend
use_case: register a service, pregnancy check, calving, or weaning, load an IATF protocol, read reproductive metrics, charge an insemination
created: 2026-07-28
modified: 2026-08-04
tags: [adr, feedlot, breeding, livestock, reproduction, event-sourced]
---

# ADR-46 — Breeding and rearing: the reproductive events (`breeding`)

## CONTEXT

> The cycle service → pregnancy check → calving → weaning, which is the heart of a breeding herd and from which pregnancy rate, calving rate, weaning rate, and calving interval emerge. Rearing needs no app: fattening the weaned animal is already modeled. What is genuinely new is reproduction.

## ASSERTIONS

1. `breeding` is four immutable reproductive events and none posts an entry except the AI charge on client livestock (rule 6). Feed and sanitary charges remain in `feed` and `sanitary`.
2. `Service`, `PregnancyCheck`, `Calving` and `Weaning` inherit from `LifecycleEvent` ([[adr-28-animal-lifecycle-and-sanitary]] rule 1): the `animal`/`lot` pair with a `CHECK` of exactly one ([[adr-26-livestock-individual-and-lot]] rule 3). Each keeps its own table and exposes `list`/`retrieve`/`create`, with no `update` or `destroy`. Individual service is on a cow; systematic IATF is loaded on a `Lot`.
3. Reproductive status — empty, serviced, pregnant, calved, dry — is derived by crossing each dam's services, checks, and calvings, and is not stored in any field. The current diagnosis is the most recent `PregnancyCheck`, and pregnancy closes with its `Calving`.
4. A `Calving` with result `live` on an individual cow creates an `Animal` (`category=calf`) and references it in `Calving.calf`. Genealogy is derived from that chain — dam from the target, sire from the service bull — and no `dam`/`sire` fields are added to `Animal` ([[adr-32-multi-rubro-assets]] rule 2). A `Calving` on a `Lot` records `births_count` without creating per-head identity.
5. `IatfProtocol` and `IatfProtocolStep` are editable catalogs with full CRUD; each step fixes a relative `day_offset` and the absolute date is derived from `Service.date`, never stored in the template. Same idiom as [[adr-40-sanitary-plan-schedule]] rules 1–2.
6. A `Service` with `method ∈ {ai, iatf}` on livestock of a `Client(kind=boarding)` posts a `debit` `concept=service` for the insemination fee, via `(source_kind="breeding_service", source_id=<Service.id>)` ([[adr-24-feedlot-domain]] rule 4), snapshotting `service_price` as of the day. Natural service, service on own livestock, and pregnancy checks, calvings, and weanings post nothing.
7. `register_service` deducts a `SemenMovement` `out` for `ai`/`iatf` and an `EmbryoMovement` `out` for `embryo_transfer` ([[adr-47-genetics-semen-embryo]]). It rejects a service on a target that is not active or belongs to another client, the absence of the exact XOR, a batch with no stock or inactive, and an inactive protocol. Late loading with a retroactive date is accepted while the target remains active.
8. `apps.metrics` derives `pregnancy_rate`, `calving_rate`, `weaning_rate`, `calving_interval` and `kg_weaned_per_dam` as pure functions ([[adr-29-metrics-derivation]] rule 1). Each returns `null` with its `not_calculable` when an input is missing, never a filler zero.
9. Rearing gains no app: the weaned animal is a normal `Animal` measured with `Weighing`, fed with `feed`, treated with `sanitary`, and placed with `PenPlacement`. The only addition is `Weaning`, with its `purpose` (`replacement` | `sale` | `undecided`).

## FORBIDDEN

- **NEVER** store reproductive status as a field (rule 3). A mutable flag falls out of sync with the events that produce it.
- **NEVER** add `dam`/`sire` to `Animal` (rule 4). Genealogy is derived from the calving → service chain, and `livestock` is not touched.
- **NEVER** store absolute dates in an `IatfProtocol` (rule 5). That would tie it to a single service and it would cease to be a template.
- **NEVER** charge for a pregnancy check, a calving, or a weaning (rule 6). The owner defined exactly one economic fact in reproduction, and modeling another is speculative.
- **NEVER** service a target that is not active or belongs to another client (rule 7). Validation lives in the service, the single write point.
- **NEVER** return 0% pregnancy rate when there were no services (rule 8). These are opposite situations and the explicit gap distinguishes them.

## REJECTED

- **A rearing app** — a parallel domain for fattening the weaned animal. Rejected by rule 9: it would duplicate `livestock` and `feed` without adding a new fact; the weaning was the only missing milestone.
- **Charging consumed semen as a service cost** — debiting the straw in addition to the fee. No: own consumption is an `out` of already-valued stock ([[adr-47-genetics-semen-embryo]] rule 6), and the only charge is the billed service.
- **A polymorphic model for the four events** — one reproductive table with a type field. Rejected for the same reason as in [[adr-28-animal-lifecycle-and-sanitary]]: nullables in every row and a type filter on every query.

## RELATED

### related adrs

- [[docs/adrs/adr-47-genetics-semen-embryo]] — the bulls, semen, and embryos the service consumes
- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — rule 1, the `LifecycleEvent` abstract
- [[docs/adrs/adr-26-livestock-individual-and-lot]] — rule 3, the animal/lot XOR
- [[docs/adrs/adr-40-sanitary-plan-schedule]] — the template + relative-calendar idiom
- [[docs/adrs/adr-29-metrics-derivation]] — the "not calculable" contract
- [[docs/adrs/adr-44-field-operational-roles]] — the RBAC gate on these routes

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `Service`, `PregnancyCheck`, `Calving`, `Weaning`, `IatfProtocol`
- [[docs/GLOSSARY-feedlot-additions]] — the reproductive names, before first use
- [[docs/API]] — the `breeding` routes
