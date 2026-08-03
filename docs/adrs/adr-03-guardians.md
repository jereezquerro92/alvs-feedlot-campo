---
title: adr-03-guardians
type: adr
category: harness
use_case: closing a batch of changes that touched PRD, the constitution, an ADR, docs/agents/, or docs/hooks/, defining or dispatching an agent, editing a guardian's watch list or the dispatch safety net, acting on a guardian verdict
created: 2026-08-02
modified: 2026-08-03
tags: [adr, harness, guardians, agents]
---

# ADR-03 — guardian agents

## CONTEXT

> Two guardians watch the health of this harness's law: `guardian-prd`
> guards the objective, `guardian-adr` guards the rules. This ADR is what
> makes their verdicts binding.

Rules only; what each guardian is — posture, watchlist, output shape — lives
in its definition under `docs/agents/`. Formerly numbered `adr-01`; renumbered
to `adr-03` on 2026-08-02 so constitution and harness tooling own `01`/`02`.
This ADR also absorbed this project's former `adr-11-guardians` on
2026-08-02 (retired as a standalone file); its surviving rule — this
project's three-guardian roster — is appended below as rule 9, per the
numbering exception recorded in [[adr-00-discipline]] REJECTED.

## ASSERTIONS

1. The two guardians — `guardian-prd` and `guardian-adr` — are the
   verification gate for their documents: [[PRD]] and the set of ADRs in
   force. One guardian per concern; adding a guardian appends a rule here.
2. SSOT for guardian definitions is `docs/agents/`. A runtime that discovers
   agents elsewhere (a `.claude/agents/` directory, an `extra_agent_dirs`
   entry) reaches them by link or reference — one real copy, links everywhere
   else.
3. Guardians are sought, not only triggered: an owner process that modifies a
   guardian's document or watched surface engages that guardian before the
   batch of changes closes. Automation that nudges the dispatch is a safety
   net for the case it forgot, and is equally binding.
4. Guardians report; they never dispatch. Sibling notification flows only
   through the owner process, which honors the returned `notify` list.
5. A guardian verdict of `violation` or `danger` blocks the change until
   resolved; `needs-new-adr` routes through the ADR lifecycle
   ([[adr-00-discipline]]), never through a local exception.
6. A guardian's output shape (`status` / `resolution` / `notify`) is fixed by
   its definition file.
7. Guardians triage before they sweep: a dispatch that touches nothing in the
   guardian's domain returns its passing verdict in one line, immediately —
   depth is spent only on plausible concerns.
8. Each guardian's watchlist has one machine copy: the `watch:` glob list in
   the frontmatter of its own definition, beside the prose that explains it.
   The dispatch safety net (`docs/hooks/guardian-dispatch`) reads only that
   key; a watched surface enters or leaves the watchlist by editing the
   guardian's file, nowhere else.
9. **This project runs three guardians**, not the harness default of two:
   `astro-drf-aws-prd`, `astro-drf-aws-adr` and `astro-drf-aws-api` — one per
   in-memory SSOT ([[PRD]], the ADR set, and [[API]] respectively). Rule 1's
   two-guardian set is the harness default, not a ceiling; a project may run
   a third guardian for a third concern it holds in memory, following the
   same rules 2–8. A verdict of `violation` / `defect` / `danger` from any of
   the three blocks exactly as rule 5 requires. Guardians run on sonnet.
   (Carried forward from this project's former `adr-11-guardians` rule 1;
   its rules 2–8 restated no new substance beyond rules 2–8 above and are
   not separately appended.)

## RELATED

### governed paths

- `docs/agents/astro-drf-aws-prd.md`, `astro-drf-aws-adr.md`,
  `astro-drf-aws-api.md` — this project's three guardians (rule 9), the
  harness-default `guardian-prd`/`guardian-adr` pair not imported
- `docs/hooks/guardian-dispatch` — the dispatch safety net (rules 3, 8)
- `docs/hooks/pre-commit` — the safety net's voice at commit time

### related files

- [[adr-00-discipline]] — the discipline both guardians enforce and obey
- [[adr-01-constitution]] — written law the guardians protect
- [[adr-02-harness]] — tooling home for agents and hooks
- [[PRD]] — the document the PRD guardian owns
- [[API]] — the document the third guardian (rule 9) owns
- [[HARNESS]] — the agent-tooling tier these definitions live in
</content>
