---
title: adr-11-guardians
type: adr
category: harness
use_case: changing PRD, an ADR, API or a watched surface, reading a guardian verdict, editing a guardian definition or its watchlist
created: 2026-07-10
modified: 2026-08-02
tags: [adr, harness, guardians]
---

# ADR-11 — guardian agents

## CONTEXT

> Three subagents hold the three in-memory SSOTs. They are engaged on purpose, they report rather than dispatch, and their blocking verdicts are binding.

## ASSERTIONS

1. The three guardians ([[GLOSSARY]]) — `astro-drf-aws-prd`, `astro-drf-aws-adr`, `astro-drf-aws-api` — are the verification gate for [[PRD]], the ADR set and [[API]] respectively. One guardian per in-memory concern; a fourth requires its [[GLOSSARY]] row and a policy change to this ADR ([[adr-00-adr-doctrine]] rule 8).
2. Their definitions live once, in `agents/`; `.claude/agents/` and `.agents/agents/` reach them by link. One real copy, links everywhere else.
3. Guardians are sought, not only triggered. A process intending to modify a guardian's SSOT or watched surface engages that guardian for the change; the `dispatch_guardians.py` nudge is the safety net for the case it forgot, and is equally binding — one dispatch per guardian per batch, before the batch closes, honoring the returned `notify` list.
4. Guardians report; they never dispatch. Sibling notification flows only through the owner process, and a guardian ignores a nudge that names itself.
5. A watchlist exists in exactly two places — the guardian's own Watchlist section and the hook's `WATCHLISTS` — identical in coverage. A divergence is a defect fixed in the batch that finds it.
6. A verdict of `violation` / `defect` / `danger` blocks the change until resolved. `needs-new-adr` routes through [[adr-00-adr-doctrine]], never through a local exception.
7. Guardians run on sonnet, and their output shape (`status` / `resolution` / `notify`) is fixed by their definition files.
8. Guardians triage before they sweep: a dispatch touching nothing in the guardian's domain returns its passing verdict in one line, immediately. Depth is spent only on plausible concerns.

## FORBIDDEN

- **NEVER** land a change against a `violation` / `defect` / `danger` verdict (rule 6). The verdict blocks until resolved, and a local exception is not a resolution.
- **NEVER** let a guardian dispatch a sibling (rule 4). Notification travels through the owner process, so one batch cannot fan out into a chain nobody is holding.
- **NEVER** edit a watchlist in one of its two homes only (rule 5). A hook watching more than the guardian claims, or less, is a gate with a hole in it.
- **NEVER** treat the dispatch nudge as the trigger to engage a guardian (rule 3). It is the safety net; the trigger is intending to touch the SSOT.

## REJECTED

- **One guardian for all three SSOTs** — cheaper per batch, and it would have read [[PRD]], the ADRs and [[API]] in one pass. It lost because the three ask different questions, and a single agent holding all of them dilutes each: the concern that fits in one context window is one SSOT. Reopening would mean the three SSOTs had merged.
- **Guardians dispatching each other** — the obvious way to propagate a finding, since a guardian already knows which sibling is affected. Rejected for the fan-out: a chain of self-dispatching agents has no bottom and no owner, so rule 4 keeps the `notify` list as data the owner process acts on.

## RELATED

### related adrs

- [[docs/adrs/adr-00-adr-doctrine]] — rule 8, the path a guardian change or a `needs-new-adr` verdict takes
- [[docs/adrs/adr-19-issue-worktree-pr]] — rule 4, the PR gate the verdicts must clear before a merge

### related files

- [[AGENTS]] — where the guardians are engaged from, and the ABC gate they enforce
- [[docs/GLOSSARY]] — the term *guardian* and the three names
- [[docs/PRD]] · [[docs/API]] — two of the three SSOTs under guard
