---
title: BDD
type: reference
status: active
created: 2026-07-10
tags: [harness, bdd]
---

# BDD — instruction manual for `docs/bdds/`

> [!note] Active
> Every user-facing feature enters here, wherever its subject exists ([[adr-07-development-flow]] r6). The template ships no `bdd-NN` entries; a project creates its own under `docs/bdds/`.

## Purpose

This directory incorporates **new features from the frontend side** — direct user requests. Every user-facing feature enters the system as a `docs/bdds/bdd-NN-slug.md` entry **before any code exists**. The entry is the agreement on behavior; code follows it.

## The flow

A BDD entry forks into two tracks:

- `bdd entry → backend half → [[TDD]] flow → …` — the backend impact section feeds one or more TDD entries, which own all backend code from there.
- `bdd entry → frontend half → test creation per [[FRONTEND]] → implementation` — frontend testing rules live in [[FRONTEND]], not here.

Both tracks converge at the shadow-test stage below.

## Entry frontmatter contract

```yaml
title: bdd-NN-slug
type: bdd
status: draft | agreed | building | shipped
created: YYYY-MM-DD
tags: [bdd]
```

- `draft` — written, not yet agreed with the requester.
- `agreed` — behavior signed off; forking into TDD/frontend work may start.
- `building` — either track in progress.
- `shipped` — shadow tests pass; feature live.

## Shadow tests

> [!important] Final validation is a real browser
> The last stage of every BDD entry replays the feature's user flows in a real browser against the rendered UI — not against components or API responses. This requires substantial browser configuration: Chromium driven over the Chrome DevTools Protocol at `127.0.0.1:9222`.

Until a project's shadow-test runner exists, a BDD entry may reach `building` but not `shipped`. Each entry specifies its flows in its *Shadow-test spec* section.

## Entry layout

Every entry follows the frontmatter contract and two-track flow above, ending in a *Shadow-test spec* section; a project's first entry sets the use-case section layout that the rest reuse.

## Naming

Sequential `NN`, kebab-case slug, English — per [[LOCALIZATION]] and [[GLOSSARY]].
