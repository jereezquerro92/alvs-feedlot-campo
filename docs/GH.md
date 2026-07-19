---
title: GH
type: reference
status: active
created: 2026-07-10
tags: [harness, github, git]
---

# GH — GitHub + git for this template

Owner: **`kodexArg`**. Repo protocol: SSH. CLI: `gh` (used directly). Ruled by [[adr-08-github-and-git]].

## Branches

| Branch | Role |
|---|---|
| **`main`** | Integration / default development. Feature PRs merge here. |
| **`prod`** | **Production.** Not `main`. Promote only from `main` (PR → `prod`). |

Forbidden as production name: treating `main` as live. Forbidden branch name for default: `master` ([[GLOSSARY]]).

## Who may push

- **Direct push to `main` and `prod`:** account **`kodexArg` only**.
- Everyone else (agents, collaborators): **branches + PRs**. No direct push to protected lines.

## How we work

1. **Issues** for work tracking — open early, close with PR. Every issue uses a repository template from `.github/ISSUE_TEMPLATE/` — the BDD/Gherkin feature form is `gh-issue-feature-bdd.md` (chooser label "Feature (BDD)"); its References section is filled liberally so no issue is orphaned for want of a link graph.
2. **PRs** for every change that lands on `main` (and every promote to `prod`).
3. Agents open branches / PRs; they do not force-push `main`/`prod` as another identity.
4. Base of feature PRs: **`main`**. Base of release/promote PRs: **`prod`** (head = `main` or release branch).

### The feature template at a glance (80-col view)

Annotated column-ruler view of `.github/ISSUE_TEMPLATE/gh-issue-feature-bdd.md`
(`!!` marks a line wider than the 80-col terminal — all prose/guidance, never
structure; GitHub wraps them):

```text
              1         2         3         4         5         6         7         8
     ....+....|....+....|....+....|....+....|....+....|....+....|....+....|....+....|
  1| ---                          ╮
  2| name: Feature (BDD)          │  frontmatter: name = chooser label in GitHub,
  3| about: ...                !! │  labels=feat, assignees=kodexArg, title prefix "feat: "
  4| title: "feat: "              │  (GitHub reads THIS, not the filename)
  5| labels: feat                 │
  6| assignees: kodexArg          │
  7| ---                          ╯
  9| <!-- ...                  !! ╮  author guidance: BDD-first, language, wikilinks,
 14| -->                          ╯  issue→PR loop. Not shown in the rendered issue.
 16| ## Story                     ╮  who / what / so-that + verbatim quote of the ask
 23| > "<...textual>"             ╯
 25| ## Scenario(s)               ╮  Gherkin Given/When/Then; comment invites a
 37| ```                          ╯  Scenario Outline for the negative cases
 39| ## Acceptance criteria       ╮  testable checklist; last row ties in
 43| - [ ] Shadow tests ...    !! ╯  shadow tests + guardian verdicts
 45| ## References  (star)        ╮  the star section: 4 link axes —
 47| <!-- #189 orphaned ...       │  Governing ADRs / Specs & docs / Code / Related.
 66| - [[informe-...]]            ╯  "link LIBERALLY" — born from the orphaned issue
 68| ## Notes / out of scope      ╮  what a fresh agent must NOT assume
 70| <!-- ... -->              !! ╯
```

## Labels (issues + PRs) — fixed set

Create only these; do not invent free-form labels.

| Label | Use |
|---|---|
| `bug` | Defect |
| `feat` | New capability |
| `chore` | Tooling, deps, noise cleanup |
| `docs` | Documentation / harness docs |
| `harness` | Skills, hooks, ADRs, agent config |
| `infra` | AWS, CI, deploy |
| `blocked` | Waiting on decision/input |

One primary type label per issue/PR; add `blocked` only when stuck.

## Git tags (releases)

- Format: **`vMAJOR.MINOR.PATCH`** (semver).
- Cut tags **from `prod` only** after a promote lands.
- Optional prerelease: `vX.Y.Z-rc.N` still from `prod` (or a short-lived release branch merged to `prod` first).

## CI / deploy refs

- **dev** pipelines / OIDC trust: `refs/heads/main` (and PR checks).
- **prod** pipelines / OIDC trust: `refs/heads/prod` (and tags `v*` if used).
- Detail for AWS roles: [[INFRASTRUCTURE]].

> [!note] Ephemeral reference run
> For the template's own stage-3 run the `dev ← main` pipeline is **out of scope**: `main` is the local development line, `prod` is the only branch reaching AWS, and OIDC deploy trust exists for `refs/heads/prod` only. The `dev ← main` trust above stays doctrine for real projects. Ruled by [[adr-12-ephemeral-run]].
