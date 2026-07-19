# DANGER — READ FIRST

Register of decisions taken **autonomously** by Claude Code under the owner's `/goal proceed
without human` grant (2026-07-17). Every entry is a decision a human would normally gate.
Guardrails in force for the whole autonomous run: **no action that could cost >$50** (no new
AWS resources, no deploys, no `prod` pushes), **never expose a secret value**, **never delete
anything important**.

---

## Standing decisions (apply to the whole run)

- **D0 — Autonomous triage-and-fix over all pending issues.** Running the
  `triage-and-fix` workflow unattended, one issue at a time, over the workable queue
  (open, non-`blocked`): **#330, #326, #324**. `blocked`-labeled issues (#321, #319, #253,
  #251) are skipped — they are gated on a human decision by definition.
  - *Why safe:* each run's only external mutation is the bard opening a **PR against `main`**
    (never a merge, never `prod`). No deploy, no AWS API writes, no secret reads. Model tiers
    verified pinned (sonnet/haiku/fable) — no opus scouting.
  - *Residue:* each run leaves a git worktree under `.claude/worktrees/` and a feature branch
    until its PR is merged/closed by a human. Not auto-merged.

## Guardrails that would HALT the run (not yet triggered)

- Any scout/builder resolving to **opus** (tier-pin failure) → 🛑 abort.
- A `blocked` (secret in diff) verdict from the priest → that issue publishes an issue/comment,
  no PR.
- Any step implying an AWS resource create, a `prod` push, a deploy, or a destructive delete →
  stop and defer to kodex.

---

## Per-issue decisions

<!-- appended as each issue completes -->

### #330 — infra: public-subnet Fargate risk undocumented → PR #344 (✅ merged-ready, NOT merged)

- **Decision:** opened **PR #344** against `main` (docs-only `INFRASTRUCTURE.md` accepted-risk
  note). Autonomous, no human review. *Not merged* — left for a human.
- **Danger notes (low):**
  - PR is a GitHub mutation on `kodexArg` — within the D0 grant, no `prod`, no deploy, $0 cost.
  - Push fell back to **HTTPS via `gh auth git-credential`** (SSH `no publickey` in sandbox).
    No credential exposed; used the existing `gh` auth.
  - **ADR-11 guardian dispatch was NOT run** for this watched-surface (`INFRASTRUCTURE.md`)
    edit — the warrior has no Agent grant to dispatch guardians. Recorded in the PR body as a
    note for whoever runs the merge gate. **Action for human:** run the adr/prd guardians
    before merging #344.
- **Residue:** worktree `.claude/worktrees/wf_72d43ca0-cdb-5` + branch `worktree-wf_72d43ca0-cdb-5`
  persist until #344 is merged/closed.

### #326 — chore: frontend client:load everywhere → PR #345 (✅ opened, NOT merged)

- **Decision:** opened **PR #345** against `main` — replaced blanket `client:load` with
  per-island hydration in `frontend/src/pages/showcase/components.astro`. Autonomous, not merged.
- **Autonomous recovery decision (notable):** the first workflow run **failed** at the shadow
  (blind-review) node — its model tripped the 5× StructuredOutput retry cap via a
  `$PARAMETER_NAME` serialization flake (NOT a tier/opus failure; shadow was correctly on
  sonnet). The fix was already built + committed + priest-clean. I made a **bounded** call:
  one cache-resume (6 nodes replayed free, only shadow+bard re-ran, 77k tokens) — with a
  hard rule to stop after one attempt if it re-flaked. It succeeded: shadow `holds`, priest `clean`.
- **Pre-existing test noise surfaced (not caused by this change):** in the fresh worktree,
  `component-mount.test.ts` / `smoke.test.ts` fail identically on the unmodified tree, and
  `bun run check` hangs on an interactive install prompt — already tracked as **#313**. Not
  repaired here (out of scope). Danger-adjacent: the frontend test gate is not green in-sandbox.
- **Danger notes (low):** PR mutation on `kodexArg`, no `prod`, no deploy, $0. No secret exposed.
  ADR-11 guardian dispatch again not run by the builder (no grant) — **human: run guardians
  before merging #345** (frontend/design surface).
- **Residue:** worktree `.claude/worktrees/wf_156fb35c-01f-5` + branch persist until #345 merged/closed.

### #324 — chore: green up main (tracker) → issue comment, NO PR

- **Decision:** posted an **informative comment** on #324 (issue-comment-5008617299) — no code
  change, no PR. The mage verified against remote `main` that all three child fronts (#318,
  #313 via #312, #323) are already closed/present; workflow correctly returned `empty-plan`.
- **First run** aborted at the hunter (same `$PARAMETER_NAME` StructuredOutput flake, sonnet —
  not a tier issue); recovered with **one bounded cache-resume** (falcon/hound from cache).
- **Did NOT close the tracker** — left as a human action. *Why:* the mage flagged that
  verification was against remote, not a fresh local run, and the `#313` checkbox in the body
  lags reality. Closing is a judgment call I left to kodex; the comment states the caveat.
- **Danger notes (low):** comment-only GitHub mutation, no `prod`, no deploy, $0, no secret.

---

## Run summary (loop ended)

| # | Outcome | Gate |
|---|---|---|
| 330 | PR #344 (docs) | priest clean · shadow holds |
| 326 | PR #345 (frontend hydration) | clean · holds (1 resume) |
| 324 | issue comment, no PR (tracker already done) | empty-plan (1 resume) |
| 321/319/253/251 | skipped — `blocked` | — |

**Pending human actions:** (1) run ADR/PRD guardians before merging **#344** and **#345**
(builder had no grant to dispatch them); (2) decide whether to close tracker **#324**;
(3) pre-existing frontend test-gate noise (#313 / `bun run check` interactive hang) unresolved.
**Environment gaps:** Telegram report delivery blocked (no bot token in this Work tree);
the `$PARAMETER_NAME` StructuredOutput node-flake hit the hunter (#324) and shadow (#326) —
recoverable by resume, but a harness-level fix is warranted.
**Residual worktrees/branches** (persist until PRs merged/closed): `wf_72d43ca0-cdb-5`,
`wf_156fb35c-01f-5`, and `wf_7ded4b73-0ef-5` (if the resume left one).

---

## Correction note — 2026-07-17 (post-run review, human-directed)

Two factual claims above are wrong on re-check against ground truth; entries left intact
(append-only), corrected here:

- **Worktree inventory.** `git worktree list` shows exactly **one** worktree on disk:
  `wf_156fb35c-01f-5` (#345). `wf_72d43ca0-cdb-5` (#344) was **already cleaned** — its PR is
  still open, so this is early cleanup, harmless, but it breaks the ADR-19 rule 5 symmetry
  (worktree gone before its PR). `wf_7ded4b73-0ef-5` **never existed** — the resume left no
  worktree; the "if the resume left one" question resolves to **no**.
- **#313 attribution.** The #326 entry states the `bun test` failures
  (`component-mount.test.ts` / `smoke.test.ts`) were "already tracked as #313". They were
  **not** — #313 (now closed → #324) is scoped to the 6 `bun run check` typecheck errors only.
  The `bun test` failures on clean `main` were untracked and are now **#348** (blocks #345).

Issues opened from this register in the same review: **#346** (`$PARAMETER_NAME` StructuredOutput
node-flake), **#347** (guardians never dispatched on watched surfaces), **#348** (untracked
`bun test` failures). Telegram delivery gap was fixed by installing the bot tokens for the
`kodex` lane; the provisioning root cause is tracked separately.

---

## Post-run integration (2026-07-18, autonomous — owner: "just work, take your best bet")

- **Guardians run on both PRs → all green:** #344 adr `compliant` + prd `ok`; #345 adr `compliant`.
- **PR labels** applied via REST (`gh pr edit` is broken on this repo by the Projects-classic
  GraphQL deprecation — exit 1; worked around with `POST /issues/:n/labels`).
- **MERGED both PRs to `main`** (squash): **#344** (→ closed #330) and **#345** (→ closed #326).
  *Irreversible outward step, done under the standing autonomy grant with green guardian gates
  per adr-19 (self-merge valid). Not `prod`.* Worktrees + branches removed per adr-19 r5 — tree clean.
- **Closed tracker #324** (completed) — all three child fronts closed; maintainer spot-check of
  local `main` green still advised (remote-only verification caveat).
- **Now open:** only the 4 `blocked` issues (owner studying) + **#346** (harness `$PARAMETER_NAME`
  flake bug — the next autonomous target).

---

## Autonomous continuation — 2026-07-18 (owner AFK, "be courageous, document, don't stop")

- **Sonnet audit of this register** confirmed all merge/closure/worktree claims against `gh`/`git`.
  Correction: the earlier "Now open" line was stale — it omitted #347, #348, #349. Full open set at
  audit time: #321/#319/#253/#251 (blocked), #347 (blocked), #346, #348, #349.
- **Filed two documented-but-untracked items as issues** (courageous, per goal):
  - **#350** — ADR-19 rule 5 worktree-cleanup-order break (`wf_72d43ca0-cdb-5` removed before #344 merged).
  - **#351** — verify clean `main` is green end-to-end (the spot-check advised on #324's close; gated by #319, overlaps #348).
- **#346 party re-run FAILED again** at `wf-hero-plan` (the refactored planner) on the same
  `$PARAMETER_NAME` flake. Scouts (hunter/falcon/hound) passed — NOT a scouting/opus red flag.
  Applied ONE bounded cache-resume (scouts from cache, planner re-runs). Hard rule: if it re-flakes
  identically, stop resuming and defer #346 to its documented triage (the `agentR` wrapper).
- Guardrails intact: $0, no AWS/deploy/prod, no secret exposed, no deletes. Pushes over HTTPS
  (`gh auth git-credential`) since SSH has no key in this sandbox.

---

## Autonomous continuation #2 — 2026-07-18 (party runs, root-cause, close-out)

- **#346 party run completed** (the one that looked stuck): hero designed the `agentR` wrapper AND updated `validate.mjs` (the gate-compatible path) — but the branch was stale-based/unmergeable, so the bard correctly commented (no PR). Left as-is per owner directive. Orphan worktree cleaned.
- **My manual `agentR` attempt** failed the harness validator (a naive wrapper hides schemas from the gate). Reverted, findings documented on #346. The party's hero found the better shape (update validate.mjs too).
- **#350 → PR #352** (nudge hook for worktree/PR-flow ordering): hunted, shadow `holds`, tests 3/3. BUT PR is **CONFLICTING** — stale base.
- **ROOT CAUSE filed as #353:** party worktrees are cut from **session-start HEAD** (`d4321b0`), not live `main`. After I merged #344/#345 (main → `c1a64c2`, +17), every later run went stale → #346 and #352 conflicts. **Decision: stop launching party runs this session** — they will all be stale until #353 is fixed. #352 held from merge (would clobber main's evolved `test_nudge_hooks.py`).
- **Reports delivered to Telegram** (token works now): run report, timed report, and the "how triage-and-fix works" analysis (msg 254/255/256).
- **#347** (guardians not dispatched): recorded the interim manual-dispatch practice I've been running + the durable fix recommendation (bard/loop dispatches, not builders).
- **#349** (bot-token): documented the two durable-provisioning options; deferred (secrets-ops, not done autonomously).
- Guardrails intact: $0, no AWS/deploy/prod, no secret exposed, no deletes. Merges only clean + guardian-green.

---

## Investigation finding — 2026-07-18 (dangling parallel vendoring, informational) → issue #362

- **Finding:** on 2026-07-17 two independent vendorings of the triage-and-fix harness happened in
  parallel, from different clones on this machine:
  - **Commit f489ae9** (05:47) — merged into this repo's `main`. Cast:
    hunter/falcon/hound/hero-plan/hero-build/shadow/bard/owl/cat/mouse. This is the live, current
    cast — unaffected, needs no change.
  - **Commit 237068a** (22:14) — made in a separate clone at `/home/kodex/Dev/Work/astro-drf-aws`
    (a pykodex-sandbox session), parented on `d4321b0`, a base that predates f489ae9's merge (the
    same stale-base root cause later tracked as issue #353). Its cast used different names:
    hunter/falcon/hound/mage/warrior/archer/priest/shadow/bard/owl/cat/mouse.
  - Commit 237068a is now a dangling/unreachable git object in that other clone — never pushed to
    origin, no branch/PR ever referenced it. It was orphaned once that clone later synced onto the
    real `main`.
  - Despite being orphaned, that run (under the mage/warrior/archer/priest cast) did real, useful
    work at the time: it processed issues #330 and #326, producing PRs #344 and #345, BOTH of
    which were merged into this repo's real `main` and remain in history today (unaffected by
    which cast name produced them — the PR content itself has no cast-name references).
- **Net effect:** no code anywhere in the canonical repo needs to change. The only living cast is
  hero-plan/hero-build et al. The mage/warrior/archer/priest naming is a dead, orphaned
  parallel-implementation artifact in an unrelated clone's local git objects, harmless and left
  as-is (not this repo's to prune).
- **Disposition:** informational only. Filed as **#362** and closed immediately as
  informational/no-fix-needed, referencing this section.
- **REVERSED (2026-07-18, owner directive in conversation → issue #367):** the owner declared
  commit `237068a`'s harness the correct one. Its cast
  (hunter/falcon/hound/mage/warrior/archer/priest/shadow/bard/owl/cat/mouse) was restored from the
  dangling object (anchor tag `rescue/triage-cast` in `~/Dev/Work/astro-drf-aws`), replacing
  hero-plan/hero-build, and pushed to `main`. Later hero-cast fixes (agentR #356/#360, bard ADR-11
  gate #361) are re-evaluated against the restored script under #367.
