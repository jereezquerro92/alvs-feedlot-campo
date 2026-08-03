# Specialized Subagents (orch-* battery)

An extensible battery of task-specific workers, distinct from the generic effort tiers (`orch-low/medium/high`). Naming convention: **every specialized tool starts with `orch-`**. Add new ones here as the battery grows.

**Model policy**: sonnet is the default for every specialized worker below. Fable and opus are disallowed in this battery; the sole exception is `orch-high` (see SKILL.md), which is not a specialized worker but an effort tier.

## Velocity loop: orch-planner / orch-builder / orch-auditor

The default build loop for non-trivial work (all sonnet). See SKILL.md "The Velocity Loop" for the full contract. Summary:

- **orch-planner** — read-mostly (may scout). Plans before any code changes; returns the plan + the exact hot-file list. Also the re-entry point after an audit: checks the finding for steering drift before re-dispatching the builder.
- **orch-builder** — write. Tests first, then code (code-only for scripts with no meaningful test surface). Consumes the planner's plan and hot-file list verbatim; does not re-scope.
- **orch-auditor** — read-only, runs with a CLEAN context (no builder narrative carried in). Validates the artifact against acceptance criteria independently; returns `verdict: pass|fail|drift`.

Routing is fixed: builder → auditor → **planner** → builder. The auditor never talks to the builder directly — that's what lets the planner catch drift before burning another build cycle.

## Per-iteration doctrine

After EVERY orchestrator iteration that produced file changes, the orchestrator MUST close the iteration by dispatching `orch-changelog` (haiku, `run_in_background: true`, non-blocking). The orchestrator no longer hand-writes commits or changelog entries itself.

On startup the orchestrator reads `AGENTS.md` then `CHANGELOG.md` (canonical format below) to learn project state.

## orch-janitor

Specialized deletion worker. model: sonnet. Works **in place (no worktree)** — it self-commits the files it modified, so a worktree would break the push.

Dispatch contract — provide exactly three things:
1. `kind` — `variable` | `function` | `class` (`function` covers functionality/feature-level removal)
2. `file_or_path` — the file, OR at minimum a search path
3. A tweet-length (≤280 char) one-line description of what that code is/does

With only those three it works autonomously: greps/globs all usages first, removes references in dependency order then the definition, never deletes a usage it cannot confidently attribute (lists those as untouched suspects), then self-commits with a subject containing the literal token `[JANITOR]`. If not a git repo or commit impossible it records that and does not fail.

Preferred for any "delete X / remove dead code" request — keeps that work out of the orchestrator's context.

Frozen JSON result schema (keys stable forever):

```json
{"target":{"kind":"","name":"","file_or_path":""},"usages_checked":0,"deleted":[{"file":"","lines":"","what":""}],"references_removed":[{"file":"","lines":"","what":""}],"untouched_suspects":[{"file":"","reason":""}],"commit":{"made":false,"sha":"","message":""}}
```

Quick Exit if any of kind/path/description is missing.

## orch-changelog

Non-blocking changelog+commit closer. model: haiku. Dispatched `run_in_background` at the end of any changed iteration. **Mechanical transcription, not judgment** — the orchestrator already knows the diff and hands it over **pre-grouped** (one block per logical group, usually just one); the closer does NOT cluster or re-attribute the diff itself. It locates CHANGELOG.md at repo root (creates if absent), records its path, appends one block per handed-in group to `## [Unreleased]`, makes one git commit per group mirroring its block, and pushes via the `kodexArg` GitHub account. If more than one group was committed, returns `status:true` but `resolution` warns that multiple commits were pushed.

Frozen canonical CHANGELOG format (verbatim — must match orch-changelog.md byte-for-byte):

```
## [Unreleased]
- group: <kebab short name>
  priority: critical|high|normal|low
  commit: <short-sha|pending>
  changes:
    - <feat|fix|refactor|remove|chore|docs>(<scope>): <one-line summary>
```

Released sections use `## [x.y.z] - YYYY-MM-DD` with the same indented group blocks. `## [Unreleased]` is always present at top, directly below `# Changelog`.

## orch-critic

Adversarial verification worker. model: sonnet. Read-only (runs checks/tests, never edits product code). Its job is to REFUTE a producing worker's claim, not endorse it. Dispatch with three things: the claim/output under test, its acceptance criteria, and a budget (max attempts/tokens). It returns a `witness_found` flag plus the witness (repro steps + violated criterion) when it breaks the claim.

Result semantics: `status:false` + `witness_found:true` = claim REFUTED (a successful critic run). `status:true` + `witness_found:false` = critique-resilient within budget. Convergence of a generation↔critique loop is "no witness found within budget" — see the adversarial-verification pattern in patterns.md. Use for security-sensitive, migration, or public-behavior changes where "looks done" is insufficient; skip for trivial work.

## orch-document-this

Documentation worker. model: sonnet. Dispatch whenever something worth persisting surfaces (a decision, a discovered fact, a config, reference knowledge) — don't let durable knowledge evaporate into chat. Input: free-text of what to document, plus an optional scope hint.

It decides the target itself:
- **Global → `~/Documents/`** — the machine SSOT vault (root IS `~/Documents/`), read by kodex AND Ada (Hermes). OS/system decisions, cross-project knowledge, reference, catalogs. Default when scope is ambiguous. Writes Obsidian Flavored Markdown (invokes `obsidian-markdown` first); links the new note from the nearest MOC (`Home.md`, `System/System.md`).
- **Local → `<repo>/docs/`** — facts true only inside one project. Plain GitHub Markdown.
- OS/system/config decisions → mini-ADR at `~/Documents/System/ADRs/YYYYMMDD-<slug>.md`. This is the one ADR home (replaced the former repo `docs/ADRs/`).

One topic per note; greps first and UPDATES in place rather than duplicating. Returns `status`/`resolution` frontmatter plus `scope` + `path`. Quick Exit when there is nothing concrete to persist.
