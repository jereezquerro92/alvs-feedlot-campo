---
category: harness
created: '2026-08-03'
modified: '2026-08-03'
tags:
- harness
- triage-and-fix
- labels
- github
title: disposition
type: reference
use_case: labeling a triage-and-fix stop-exit so the issue does not loop
---

# disposition.md — issue stop labels (anti-loop)

The problem: a party run that only **comments** and leaves the issue unlabeled gets
picked up again on the next hunt — same exits, same tokens, no progress.

The answer: every stop-exit applies **exactly one** disposition label from [[GH]],
comments the reason, and the hunter **refuses to re-hunt** while that label remains.

Label SSOT (names, meanings, colors): [[GH]]. This file is the party's wiring.

## The five disposition labels

| Label | When the party applies it | Comment must say |
|---|---|---|
| `needs-info` | Issue lacks requirements / acceptance criteria / a decidable ask | What is missing; questions for the human |
| `blocked` | Unmet `Requires PR: #N`, ground unfit that may clear, waiting on a decision | What it waits on |
| `deferred` | Too complex for one party run; PR cascade; recurring-defect (vampiro) | Why called off; what re-scope would unblock |
| `unresolvable` | Constitution forbids; permanent out of scope; confirmed will-not-fix | File+rule or permanent reason — **this is the clear "not resolvable" signal** |
| `duplicate` | Falcon `emergencia` (confirmed duplicate) | Canonical issue/PR number |

Never use `unresolvable` for missing info, complexity, or a PR that might still merge.

## Re-entry rule (binding)

If the issue already carries any disposition label above → quick-exit
`already-dispositioned`. Do **not** plan, build, or comment beyond a one-line note that
the label still holds. A human removes the label (and answers / re-scopes) before the
next hunt.

Exception: none for agents. Owner override is removing the label by hand.

## Exit → label map (orchestrator / bard)

| Quick-exit or plaza outcome | Label | Notes |
|---|---|---|
| `already-dispositioned` | *(keep existing)* | No mutation |
| `requirement-unmet` | `blocked` | **Not** `deferred` — the requirement may still land |
| Vague / incomplete issue body | `needs-info` | Ask; stop |
| `hard`/`large` plan refuses or needs split beyond one hunt | `deferred` | Complexity |
| `outOfScope: recurring-defect` (vampiro) | `deferred` | Needs human diagnosis |
| `constitutionOk: false` (law forbids) | `unresolvable` | Cite file+rule |
| Permanent out of scope / wontfix | `unresolvable` | |
| Falcon `emergencia` | `duplicate` | |
| `stackDepsOk` / `ghConnected` false | `blocked` | Environment may clear |
| Priest `blocked` / publish miss with no commits | comment only | No disposition unless a row above fits |

Applying a disposition label **replaces** any previous disposition label on that issue
(one at a time). Type labels (`bug`/`feat`/…) stay.

## Who mutates

- **Bard** applies the label on plaza when `hunted: false` and a disposition fits.
- **Orchestrator (you)** applies it on forest/tavern quick-exits before plaza — same
  `gh issue edit <n> --add-label <label>` (and `--remove-label` on the prior disposition
  if present). Create the label on the repo if missing (`gh label create`), using the
  color hints in [[GH]].

## Relation to PR `deferred` / `requires:N`

PR-side REQUIREMENTs stay in `references/deps.md`. An **issue** waiting on a PR gets
`blocked`, not `deferred`. A **PR** doomed by cascade gets `deferred` via `kwf-deps`.