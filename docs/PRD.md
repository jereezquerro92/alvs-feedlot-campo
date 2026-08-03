---
title: PRD
type: prd
category: project
use_case: checking a change against the product objective
created: 2026-07-10
modified: 2026-08-02
tags: [doc, prd, ssot, feedlot, livestock, traceability]
---

# PRD — feedlot operations

> [!important] Always in memory
> This file and [[API]] are the two documents every agent holds in memory at all times. The ABC gate lives in [[AGENTS]]: follows PRD? complies with ADRs? modifies API?

## The objective

- **Every input reaches the animal it was applied to and the owner who pays for it.** A feedlot feeds its own cattle and, in the same pens, other people's — boarding. The moment two owners share a yard, a kilo of ration and a dose of vaccine stop being a cost and become a fact that must be attributed. The objective is that nothing an animal receives is recorded without both of its answers: which animal, and whose. An input that cannot say whose it was is not a record, it is a loss.

- **The operation and the account are one record.** Feeding, treating, working a pivot, servicing a machine — each ends as a movement against a client's current account, at the price of the day it happened. The account is not an accounting product bolted on afterwards and reconciled by hand at month's end; it is the settlement side of the very events the operation already writes. What was charged and what was done are the same trail read from two directions.

- **What was spent is read against what was produced.** Recording an input is only worth the effort if it can be asked what it bought. Gain, conversion, mortality, the sale at the end — the operational history exists so that cost and outcome can be put side by side, per animal, per lot, per client, without anyone rebuilding the numbers by hand.

- **Every role sees the operation it answers for, and no more.** The people around a feedlot are not one audience: the owner, the field administration, whoever runs the yard, whoever loads the mixer, the workshop, and the cattle owners themselves. Some of them must never see the rest — a client sees their own cattle and their own account, never another's. What a user may see or do follows from their role, never from which screen they reached.

- **It grows one domain at a time.** The feedlot is where this started, not where it ends. Crops and machinery already run on the same spine, charging the same account through the same seam. A new domain is an addition, not a reform: it composes onto the harness rather than changing it.

## The domains

The operational scope. The spine is shared by every domain; the domains stand on it and on each other only where the business genuinely connects them.

| Group | Domain | What it covers |
|---|---|---|
| spine | `clients`, `ledger`, `assets`, `market`, `fx` | who is charged, the immutable current account they are charged in, the shared asset/costed-event abstractions a new domain inherits, reference prices and currency |
| cattle | `livestock`, `feed`, `feedyard`, `sanitary`, `traceability` | the animal and the lot through their whole life — intake, pens and rations, feeding, health and the sanitary plan, and the regulatory identity and movement record |
| herd | `breeding`, `genetics` | reproduction, and the semen and embryo inventory with the breeding values behind it |
| other domains | `crops`, `machinery` | alfalfa on irrigation pivots with its cuttings and field tasks, and the machine fleet with its maintenance |
| across all | `metrics`, `expenses`, `inventory`, `weather`, `notifications`, `advisors`, `assistant` | the derived reading of everything above, the costs that are not an input, stock and conditions, what gets pushed to whom, and the AI layers over a client's own numbers |

This table states scope, not specification. Each domain's depth — how a debit is priced, what a lifecycle event forbids, how a metric is derived — belongs to [[FEEDLOT]], [[FEEDLOT-DATA-MODEL]], the ADRs that rule them, and the domain's [[TDD]] entries.

## Who uses it

The people around a feedlot are not one audience: whoever owns or administers the operation, whoever runs the yard or loads the mixer, the workshop, and the cattle owners themselves — a client reaches only their own cattle and their own account, never another's (objective 4 above). The exact roles, what each answers for, and the Group that enforces it are owned by [[AUTH]] and [[adr-44-field-operational-roles]].

## What it is

Two Docker services on Fargate — a Django backend and an Astro frontend — connected to state through PostgreSQL and to AI through the layers the harness carries: a zero-generation router for moving through a system that keeps growing ([[CHATBOT]]), generative advisors and a conversational assistant confined to a client's own data ([[adr-27-advisors-generative]], [[adr-35-conversational-assistant]]), and app-only Microsoft Graph access for a Microsoft 365 estate ([[adr-13-m365-graph]]). Those are means. The objective is above them, and a means that stops serving it is removed, not defended.

## The harness

The harness is the support of the objective, not the objective. It rests, in this order, on:

1. **This PRD** — the objective every change is measured against.
2. **The ADRs** (`docs/adrs/`) — the standing rules; each states what is in force and links the doc that owns the detail.
3. **[[API]]** — key: the only source of valid endpoints; nothing enters the backend except through a row here.
4. **The docs** (`docs/`) — one SSOT per topic; every fact is stated once, where it lives, and linked from everywhere else.

The workflow for agents is highly typified and prepared: [[DEVELOPMENT-LOOP]] carries the exact sequence — and the tool or skill at each step — for adding any new element, from idea to merged PR. Other documents are linked from these four surfaces as the need appears; they do not need to be indexed here.

## The horizon

- It **grows by addition**: a new capability is a new domain app and its routes, inheriting the spine rather than duplicating it; the harness stays as it is.
- The **record stays trustworthy, always.** Nothing once logged is ever falsified or discarded to make room for a future feature — the invariant is ADR-bound ([[adr-24-feedlot-domain]], [[adr-25-account-ledger]]), never a local convenience.
- It stays **agnostic to company, farm and account.** The product describes what a feedlot does, never what one feedlot does — no client, herd, establishment, brand or account identifier belongs in code or in docs. Those values arrive as data the users load, or through [[VARIABLES]] (the only inventory of environment variables; secrets live in Secrets Manager).
- It stays **agnostic to which domains a deployment runs.** An installation that only feeds cattle and one that also cuts alfalfa are the same product with a different set of domains enabled; neither is a fork, a branch, or a special case.
