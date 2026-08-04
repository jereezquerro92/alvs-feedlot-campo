---
title: adr-04-issue-delivery
type: adr
category: harness
use_case: running a GitHub issue through delivery, wiring or changing the triage party, cloning a project that will use issue delivery, closing a party run that touched law or assertions
created: 2026-08-02
modified: 2026-08-03
tags: [adr, harness, triage-and-fix, delivery, assertions]
---

# ADR-04 — issue delivery (triage-and-fix)

## CONTEXT

> This harness owns both the law and the delivery cast. One SSOT tree.
> Runtimes differ; the phases, contracts, and assertion duties do not.

Rules only. Phase names, dispatch maps, and operator wiring live in the
documents listed under RELATED — not in this ADR. Formerly numbered
`adr-02`; renumbered to `adr-04` on 2026-08-02 so constitution and harness
tooling own `01`/`02`. This ADR governs the automated `kwf-*` delivery
pipeline; [[adr-19-issue-worktree-pr]] governs this project's manual
git issue→worktree→PR mechanics and is deliberately kept separate — see
that ADR's own RELATED for the cross-link back.

## ASSERTIONS

1. GitHub issue delivery ships **in this repository**: skill
   `docs/skills/triage-and-fix/`, cast `docs/agents/kwf-*.md`, deps CLI
   `docs/skills/triage-and-fix/bin/kwf-deps`. That tree is the SSOT — not a
   sibling checkout.
2. **Include, adapt by runtime.** The playbook and YAML contracts are
   runtime-agnostic. Model pins and spawn mechanics live in
   `docs/skills/triage-and-fix/references/runtimes.md` (Kimi, Claude Code,
   Cursor/Grok). A runtime may lack a native `kwf-*` registry; it still runs
   the same phases by injecting the agent files as prompts.
3. Doctrine-first planning is binding: PRD and ADRs in force before a plan;
   inquisitor before camp. That duty does not replace [[adr-03-guardians]] —
   guardians still gate law changes after publish.
4. After plaza / bard publishes, the **owner process** closes the batch: run
   `docs/hooks/guardian-dispatch --bundle <baseRef>` against the delivered
   change set ([[adr-03-guardians]] rule 10); paste the bundle payload into
   each guardian's prompt and dispatch all owed guardians in one turn; honor
   `violation` / `danger` / `needs-new-adr` per [[adr-03-guardians]].
5. When a plan slice or delivered diff touches `docs/assertions/` or claims
   to satisfy an assertion law, builders follow [[TDD]] and the
   `assertion-review` skill: proving tests first, linked under `### Tests`,
   then the code. The inquisitor treats "touches assertions without a TDD
   step" as a plan `violation`. The owner process runs `assertion-review`
   on those assertions before the batch closes.
6. Unmet assertion laws do not block unrelated issues. They block (or
   redirect into TDD) only work that claims those laws or edits their
   files — hunter `constitutionOk` / camp deviations record the block;
   inventing a new assertion without the owner is forbidden
   ([[assertion-00-discipline]]).
7. **Assertions are the entry path for important new features.** Delivery
   may land ordinary fixes without an assertion; any feature the owner
   elevates to a lasting promise enters as an assertion law, then tests,
   then code — never code-first against a silent wish.
8. **Stop-exits label the issue.** Every party exit that does not publish a
   PR applies exactly one disposition label from [[GH]]
   (`needs-info` | `blocked` | `deferred` | `unresolvable` | `duplicate`)
   and comments the reason. Detail and exit→label map:
   `docs/skills/triage-and-fix/references/disposition.md`. An issue that
   already carries any of those labels is not re-hunted until a human
   removes the label. `unresolvable` is the permanent-no signal — never use
   it for missing requirements, complexity, or a PR that may still merge.

## FORBIDDEN

- **NEVER** keep a second SSOT for the cast outside this tree (rule 1). A
  historical sibling may mirror or point here; it must not diverge as a
  competing source of truth.
- **NEVER** treat a bard PR as batch-closed when `guardian-dispatch` named
  a guardian that was not run (rule 4).
- **NEVER** mark an assertion `verified` from a party run without proving
  tests per [[TDD]] (rule 5).
- **NEVER** leave a stop-exit as a comment-only with no disposition label
  (rule 8). An unlabeled stop is how the same issue loops through the party.
- **NEVER** label `unresolvable` when the real state is waiting, missing
  requirements, or complexity (rule 8) — those are `blocked`, `needs-info`,
  and `deferred`.

## REJECTED

- **Name-only post-bard dispatch** — post-bard step called
  `docs/hooks/guardian-dispatch <baseRef>` without `--bundle`; dispatched
  guardians received only the changed-file list, no diff, no adr_index.
  Superseded 2026-08-03 by rule 4's `--bundle` form ([[adr-03-guardians]]
  rule 10): the owner delivers the full payload in one turn, guardian does
  not rediscover.
- **Compose-only sibling (no cast in-tree)** — keep `kwf-*` exclusively in
  `~/Dev/harness-triage-party` and discover it globally. Rejected 2026-08-02:
  the main harness must ship a working delivery path for clones; multi-runtime
  adaptation requires the cast beside the law and assertions. Reopen only if
  delivery is deliberately dropped from the template.
- **Vendoring as Kimi-only blobs with no runtime map** — copy agents without
  documenting Claude/Cursor-Grok dispatch. Rejected because the playbook's
  value is the phase contracts, not one CLI's `Agent` tool.
- **Folding this into [[adr-19-issue-worktree-pr]]** — one ADR for both the
  automated `kwf-*` pipeline and this project's manual git issue→PR shape.
  Rejected on adoption (2026-08-02): the two govern different machinery —
  an agent delivery pipeline versus git mechanics — and folding them would
  make either harder to change without touching the other. Kept separate,
  cross-linked both ways.

## RELATED

### governed paths

- `docs/skills/triage-and-fix/` — playbook, deps, disposition, runtime map
- `docs/agents/kwf-*.md` — cast (with guardians)
- `docs/hooks/guardian-dispatch` — post-bard safety net entry
- `docs/skills/assertion-review/` — assertion close-out
- `docs/CLONE.md` — clone checklist including delivery wiring

### related files

- [[adr-01-constitution]] — assertions as feature entry path
- [[adr-02-harness]] — skills/agents home
- [[adr-03-guardians]] — guardian duty the post-bard step honors
- [[adr-08-github-and-git]] — labels only from [[GH]] (rule 7)
- [[adr-19-issue-worktree-pr]] — this project's manual git issue→PR shape,
  kept separate and cross-linked
- [[GH]] — fixed label set including disposition stop labels
- [[assertion-00-discipline]] — laws camp/assertion-review must pass
- [[TDD]] — test-first path when assertions are in play
- [[HARNESS]] — delivery model in prose
- [[CLONE]] — operator steps
</content>
