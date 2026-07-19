---
created: '2026-07-10'
status: active
tags:
- prd
- ssot
- sharepoint
- chatui
title: PRD
type: prd
---

# PRD — astro-drf-aws

> [!important] Always in memory
> This file and [[API]] are the two documents every agent holds in memory at all times. The ABC gate lives in [[AGENTS]]: follows PRD? complies with ADRs? modifies API?

## The objective

- **Connect SharePoint securely through AWS.** Company information leaves the Microsoft 365 / SharePoint estate and reaches the web only through this authenticated tier, under its own RBAC — never directly, never anonymously.
- **A solid ChatUI that keeps growing.** A chat surface whose router is very safe from the start: it offers "go to"-style actions — the most used — to move through a site that is itself growing, using **phrases** the LLM compares against the user's prompt to find the best route; the phrases grow because they are loaded in the database — new routes are new rows, not new code. Mechanism and its guardrails: [[CHATBOT]].
- **New apps keep flourishing.** The harness stays solid at all times so that new apps can be built on it, each with the same objective: from SharePoint to the Web — today as dashboards, tomorrow as further tools.

## What it is

Two Docker services on Fargate — a Django backend and an Astro frontend — connected to state through PostgreSQL and connected to AI, and supported the whole way by the harness below.

## The harness

The harness is the support of the objective, not the objective. It rests, in this order, on:

1. **This PRD** — the objective every change is measured against.
2. **The ADRs** (`docs/adrs/`) — the standing rules; each states what is in force and links the doc that owns the detail.
3. **[[API]]** — key: the only source of valid endpoints; nothing enters the backend except through a row here.
4. **The docs** (`docs/`) — one SSOT per topic; every fact is stated once, where it lives, and linked from everywhere else.

The workflow for agents is highly typified and prepared: [[DEVELOPMENT-LOOP]] carries the exact sequence — and the tool or skill at each step — for adding any new element, from idea to merged PR. Other documents are linked from these four surfaces as the need appears; they do not need to be indexed here.

## The horizon

- It **grows by addition**: a new capability is a new domain app and its routes; the harness stays as it is.
- It stays **agnostic to company and to account** — every such value arrives through [[VARIABLES]] (the only inventory of environment variables; secrets live in Secrets Manager) and never in code or docs.
