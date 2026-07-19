---
title: bdd-00-template
type: bdd
status: draft
created: 2026-07-14
tags: [bdd, template]
---

# bdd-00 — template

> [!note] Skeleton, not an entry
> A project copies this file to `bdd-NN-slug.md` (sequential `NN`, kebab-case
> slug) and fills it. The `-00-` file is never implemented and never leaves
> `draft`. The flow, the frontmatter contract, and the status transitions are
> owned by [[BDD]] — read it before starting. This template ships no concrete
> `bdd-NN` entries of its own — it is scaffolding for the projects built from it.

## Use case

As a `<role>`, when I `<action>`, I see `<observable outcome>` — the behavior
agreed before any code exists.

## Frontend half

The Astro/Svelte/HTMX surface: pages, components, the interactivity rung
climbed ([[adr-04-frontend-and-design-system]]), design-system compliance
([[DESIGN-SYSTEM]]), variables consumed (`PUBLIC_*` only — [[VARIABLES]]).

## Backend half

The backend impact, if any. Each new endpoint feeds one or more [[TDD]]
entries; link them here. `None` when the feature reuses existing [[API]] rows.

## Error handling

What the user sees on failure — fallbacks, status codes, `Cache-Control`.

## Shadow-test spec

The user flows a real browser replays against the rendered UI ([[BDD]]). Until
a project's shadow-test runner exists, an entry may reach `building`, never
`shipped`.
