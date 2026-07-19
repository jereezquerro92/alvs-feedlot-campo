---
title: adr-11-guardians
type: adr
status: active
created: 2026-07-10
tags: [adr, harness, guardians]
---

# ADR-11 — guardian agents

Rules only; content lives in [[AGENTS]], [[GLOSSARY]], and the agent definitions under `agents/`.

1. The three guardians ([[GLOSSARY]]: guardian) — `astro-drf-aws-prd`, `astro-drf-aws-adr`, `astro-drf-aws-api` — are the verification gate for their SSOTs: [[PRD]], the active ADR set, and [[API]] respectively. One guardian per in-memory concern; adding a guardian requires its GLOSSARY row and a supersession of this ADR ([[adr-00-adr-doctrine]]).
2. SSOT for their definitions is `agents/`; `.claude/agents/` and `.agents/agents/` are links to it. One real copy, links everywhere else.
3. Guardians are sought, not only triggered. An owner process that intends to modify a guardian's SSOT or watched surface engages that guardian for the change; the `dispatch_guardians.py` nudge is the safety net for the case it forgot, and is equally binding — one dispatch per guardian per batch, before the batch closes, honoring the returned `notify` list.
4. Guardians report; they never dispatch. Sibling notification flows only through the owner process. A guardian ignores dispatch nudges that name itself.
5. Watchlists exist in exactly two places — each guardian's Watchlist section and the hook's `WATCHLISTS` — and must stay identical in coverage; a divergence is a defect fixed in the same batch that finds it.
6. A guardian verdict of `violation` / `defect` / `danger` blocks the change until resolved; `needs-new-adr` routes through the [[adr-00-adr-doctrine|ADR lifecycle]], never through a local exception.
7. Guardians run on sonnet; their output shape (`status` / `resolution` / `notify`) is fixed by their definition files.
8. Guardians triage before they sweep. A dispatch that touches nothing in the guardian's domain returns its passing verdict in one line, immediately — false positives are dismissed fast; depth is spent only on plausible concerns.
