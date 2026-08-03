---
title: FEEDLOT
type: reference
category: project
use_case: understanding what the feedlot does and which app owns which fact
created: 2026-07-21
modified: 2026-08-02
tags: [doc, feedlot, domain, ssot]
---

# FEEDLOT — the farm-traceability domain

> [!note] Proposed
> This doc adds a domain on top of the template. It is a proposal until it passes
> the ABC gate ([[AGENTS]]) and the guardians ([[adr-03-guardians]]). Rules are in
> [[adr-24-feedlot-domain]], [[adr-25-account-ledger]], [[adr-26-livestock-individual-and-lot]],
> [[adr-27-advisors-generative]]. The data model is [[FEEDLOT-DATA-MODEL]].

## The objective

Traceability for a feedlot that runs **own cattle** and **boarding** (custom feeding
of third parties' cattle, billed for feed and services). Every input applied to an
animal is recorded, attributed to its owner, and cross-referenced against its outcome
(gain, conversion, mortality, sale). Everything a feedlot input touches is billed to
the owner's current account in ARS at the price of the day. The same spine later
carries other farm domains — this is [[PRD]]'s "grows by addition", instantiated.

## Domain apps

Spine (shared, reused by future domains):

- `clients` — clients and their accounts.
- `ledger` — the current account: immutable movements and payments ([[adr-25-account-ledger]]).
- `market` — reference cattle prices ([[FEEDLOT-DATA-MODEL]]).
- `advisors` — the three AI advisors ([[adr-27-advisors-generative]]).

Cattle domain (today):

- `livestock` — `Animal`, `Lot`, `Intake`, `Weighing`, `Death`, `Exit` ([[adr-26-livestock-individual-and-lot]]).
- `feed` — `FeedType`, `FeedDelivery`, `FeedStockMovement`, `FeedingEvent`.
- `health` — `HealthProduct`, `HealthEvent`.

Later additions (shipped, grow-by-addition):

- `expenses` — `ExpenseEvent`: extra charges (labor/fuel/machinery) billed to a client
  through the ledger seam, never a manual debit ([[adr-44-field-operational-roles]] decision 6).
- `assistant` — the per-client conversational asesor, read-only forever ([[adr-35-conversational-assistant]]).

App naming follows [[GLOSSARY]] (lowercase, domain-named, singular PascalCase models).
New nouns are added to [[GLOSSARY]] first (`GLOSSARY-feedlot-additions.md`).

## Business rules (summary; force in the ADRs)

### Intake — two modes ([[adr-26-livestock-individual-and-lot]])

Cattle enter either **individually** (one `Animal` per ear tag) or **as a lot**
(head count + total weight, no per-head identity). `Weighing`, `Death`, `Exit` target
an `Animal` **or** a `Lot`.

### Feed origin and costing ([[adr-25-account-ledger]])

A `FeedingEvent` records an `origin`:

- `client_stock` — decrements the client's feed stock; **no ledger charge** (the client
  already provided the feed). Still valued for consumption metrics.
- `own_stock` — decrements the feedlot's stock **and** posts a `debit` `LedgerEntry`
  (`quantity × unit_price` of the day).

Metrics value **all** consumption regardless of origin; billing charges **only**
`own_stock`. Separating billing from the consumption metric is the crux of the rule.

### Health

`HealthEvent` (vaccine/treatment) always posts a `debit` — it is a feedlot input.

### Current account ([[adr-25-account-ledger]])

An immutable ledger. Debits from feeding/health/services, credits from `Payment` and
adjustments. Sign: positive balance = client owes. No edits, no deletes — corrections
are counter-entries. Every debit snapshots `unit_price` and `quantity` (historical price).

### Advisors ([[adr-27-advisors-generative]])

Three read-only, per-client, generative analyses over the client's own metrics. A named
exception to the router's zero-generation posture ([[adr-15-chatbot-two-tier]]).

### Roles and the client portal ([[adr-44-field-operational-roles]], [[adr-45-lot-owner-assistant-access]])

Six operative field roles are Django Groups; the matrix of who reads/writes which area
lives in one file, `apps/users/roles.py` ([[adr-44-field-operational-roles]] decision 1).
`lot_owners` is a **client portal**: read-only and confined to the single `Client` bound
to its `AccessRequest`, reaching exactly three client-keyed surfaces — metrics, the account,
and the conversational asesor ([[adr-45-lot-owner-assistant-access]]). Reference market
prices (`market`) are staff-only cross-client data, shown in the redesign's *precios*
module and never scoped to a tenant. The users module is reference-only: a grant is an
admin action in `/admin/`, never self-service ([[adr-20-authorization-lobby]] rule 3).

## Localization

Domain nouns and choices are English in code ([[LOCALIZATION]]); Spanish exists only in
the frontend's rendered output through the i18n catalog. Default locale is `es`.

## Out of scope (initial phases)

Tax/AFIP invoicing, scale hardware integration, transport documents (DTe/DTA), payroll,
and the non-cattle domains — all deferred to later additions.
