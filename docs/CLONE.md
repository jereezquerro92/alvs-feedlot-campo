---
title: Clone
description: Where this project's harness stands post-adoption — code roots, hooks, vault, skills, delivery
updated: 2026-08-02
---

This is not a first-run checklist for an empty clone: alvs-feedlot-campo is
an established, built project, and this file records the *actual*
post-migration state of its harness rather than a greenfield to-do list.
Detail lives in [[HARNESS]], [[adr-02-harness]], [[adr-03-guardians]].

## 1. Code-root pair — already chosen

`backend/` + `frontend/` is this project's pair, decided at
[[adr-09-docker-compose]] rule 1. `interfaces/`/`services/` was never
adopted and does not exist here. Nothing to do.

## 2. Guardian dispatch — already wired, different mechanism

This project's guardian safety net is `.claude/hooks/dispatch_guardians.py`,
a Claude Code `PostToolUse` hook (within-session, tool-call granularity),
not the harness-default git `pre-commit` symlink. Both serve the same duty
([[adr-03-guardians]] rules 3 and 8) at different lifecycle points; only one
is wired in this repo, deliberately. `.claude/agents` and `.agents/agents`
already resolve to this project's agent SSOT.

## 3. Vault — already vendored

The `markdown-vault-docs` MCP is vendored project-locally
(`scripts/mvmcp.py`, self-bootstrapping, git-ignored `.mvmcp/`) per
[[adr-18-markdown-vault-mcp]] — a more elaborate, already-working
implementation of the same job harness-default's `markdown-vault-mcp`
server does. Not replaced by this migration.

## 4. Constitution — filled, not templated

[[PRD]], [[REQUIREMENTS]] and [[INFRASTRUCTURE]] under `docs/constitution/`
already carry this project's real content (not bracket templates) — moved
here intact by this migration, never emptied or reset. [[HARNESS]] and
[[CONVENTION]] are adopted from harness-default doctrine.
[[LOCALIZATION]] is this project's own (US spelling, Spanish-permissive
policy — deliberately not harness-default's `LOCALISATION.md`).

## 5. Skills — already vendored, real copies

`.claude/skills/` and `skills/` already carry this project's full `kdx-*`
skill set plus `obsidian-markdown`, vendored as real copies per
[[adr-02-harness]] rules 9-10 (formerly old adr-14). `assertion-review` and
`triage-and-fix` are adopted separately by the harness-asset slice of this
migration; see that slice's own report for their landing state.

## 6. Issue delivery

This project's git-level issue→PR shape is [[adr-19-issue-worktree-pr]] —
kept separate from harness-default's `kwf-*` triage-and-fix cast per
[[adr-04-issue-delivery]], cross-linked both ways. Do **not** add a product
assertion until the owner reserves compute for a law
([[assertion-00-discipline]]); none was invented by this migration.

## Done — this migration's state

Code-root pair: unchanged, already chosen. Constitution: migrated intact,
filled. Skills: already vendored. Guardian dispatch: already wired via a
different, equally binding mechanism. Vault: already vendored. Assertions:
discipline file seeded, zero product assertions — the healthy default.
