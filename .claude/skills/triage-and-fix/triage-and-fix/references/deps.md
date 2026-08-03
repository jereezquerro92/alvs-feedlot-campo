# deps.md — the PR REQUIREMENT system

The problem: an issue (or a PR) sometimes **trusts another PR, not just the code on
`main`**. Today GitHub has no way to say "do not merge me before #123" — so a deferred
prerequisite silently strands everything built on top of it.

The answer here is labels-only (owner decision): human-editable, machine-queryable, no
manifest file to merge-conflict over.

## The labels

| Label | Color | Meaning |
|---|---|---|
| `requires:<N>` | gray | This PR must not merge before PR #N. One label per requirement. |
| `deferred` | red | The hunt is called off — directly (human/label) or by cascade. |

`bin/kwf-deps` creates both on demand (`--force`-safe), so no repo bootstrap is needed.

## What "deferred" means (owner decision: either)

A PR counts as deferred when **either**:

1. it carries the `deferred` label, **or**
2. it is **closed without being merged**.

Both trigger the cascade. The close-unmerged trigger is noisier (a superseded PR can defer
its dependents) — that trade was accepted deliberately: a PR whose ground disappears
should fail loudly, and `kwf-deps lift` is the mop.

## The three moments

### 1. Intake — an issue that trusts a PR

An issue body may carry `Requires PR: #N` (or `Requires: #N, #M`). The hunter checks each
with `kwf-deps status <N>`:

- **#N merged** → requirement satisfied, hunt proceeds.
- **#N open, not deferred** → ground **unfit**: quick-exit `requirement-unmet`, comment on
  the issue naming what it waits on. The issue is **blocked, not dead** — it is NOT labeled
  `deferred`; its requirement may still land.
- **#N deferred or closed-unmerged** → same quick-exit, and the comment says the
  requirement went dead so a human can re-scope or close the issue.

### 2. Planning & building — a PR that trusts a PR

When the work builds on an unmerged PR's code, the mage sets:

- `baseRef`: the required PR's head branch — each builder's worktree branches from it, so
  the new code sits *on top of* the unmerged work;
- `prRequirements`: the required PR numbers.

At publish time the bard runs `kwf-deps requires <new-pr> <N...>`, which applies the
labels and comments the declaration on the new PR. The PR body also carries a human-
readable `Requires: #N` line — but the **label** is the machine-checked contract.

### 3. Deferral — the cascade

When any PR becomes deferred (label or close-unmerged), run:

```
bin/kwf-deps cascade <pr> [--repo owner/repo] [--dry-run]
```

It walks the requirement graph transitively over open PRs: every open PR with a
`requires:<deferred>` label gets the `deferred` label and a comment naming the requirement
that doomed it — then *its* dependents are processed, and so on. A requirement that merged
dooms nobody; the cascade only walks unmerged roots.

**Who runs it:**

- The **bard**, automatically, whenever its own action defers anything.
- **You**, by hand, after manually deferring a PR: `kwf-deps cascade <pr>`.
- **GitHub Actions**, for closes/labels done in the web UI by anyone: vendor
  `extras/gha-kwf-deps.yml` into the repo's `.github/workflows/`.

### The reverse — `lift`

Deferral is reversible. When a deferred requirement finally lands (or a close was a
mistake and the PR reopens/merges):

```
bin/kwf-deps lift <pr> [--repo owner/repo] [--dry-run]
```

removes `deferred` from every open PR whose requirements are now **all merged**. The
criterion is requirement *merge-state*, so one tier at a time unblocks: when #20 merges,
`lift` clears the PRs that required #20; PRs that required *those* keep their label until
their own requirement merges. A PR deferred for a *different* reason than requirements
keeps its label unless a human removes it — `lift` only clears PRs whose sole blocker was
the requirement chain.

## CLI reference

```
bin/kwf-deps requires <pr> <N...>   declare requirements (labels + declaration comment)
bin/kwf-deps check <pr>             exit 0 iff every requires:N on <pr> is merged; exit 2
                                    and print the unmet otherwise
bin/kwf-deps cascade <pr> [--force] defer every open PR that transitively requires <pr>;
                                    refuses unless <pr> is labeled deferred or closed
                                    unmerged (--force overrides)
bin/kwf-deps lift <pr>              un-defer what is now unblocked (fixpoint)
bin/kwf-deps status <pr>            print a PR's requirement chain with states

Global flags: --repo OWNER/REPO (default: cwd's repo), --dry-run (print planned
mutations, change nothing).
```

## Invariants

- **Requirements only make sense on open PRs.** `requires` refuses a closed/merged target.
- **A requirement on an already-merged PR is a no-op** — noted, still recorded.
- **Cycles are safe**: the cascade's `seen` set bounds the walk; two PRs that require each
  other defer together, which is the honest reading of a cycle.
- **The label is the contract, the comment is the explanation.** Nothing parses comment
  text to make decisions.
