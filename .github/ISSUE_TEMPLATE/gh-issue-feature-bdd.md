---
name: Feature (BDD)
about: A user-facing behavior, written BDD-first (Gherkin) with a rich reference graph
title: "feat: "
labels: feat
assignees: kodexArg
---

<!--
  BDD-first ([[BDD]], [[adr-07-development-flow]]). Describe the BEHAVIOR before any code.
  Language: English for structure; keep verbatim user quotes in their original language.
  Links: use Obsidian [[wikilinks]] and paths relative to the repo root (e.g. [[frontend/src/lib/...]]).
  Every change enters through this issue → PR loop ([[adr-19-issue-worktree-pr]]).
-->

## Story

**As a** <role>
**I want** <goal>
**so that** <value>

<!-- Optional: the real request, verbatim (any language). -->
> "<lo que pidió el usuario, textual>"

## Scenario(s)

```gherkin
Feature: <short feature name>

  Scenario: <the happy path in one line>
    Given <starting context>
    When  <the action>
    Then  <the observable outcome>
    And   <additional outcome>

  # Add Scenario Outline + Examples for the negative / edge cases.
```

## Acceptance criteria

- [ ] <observable, testable condition 1>
- [ ] <observable, testable condition 2>
- [ ] Shadow tests green ([[TDD]] / [[FRONTEND]]) and guardian verdicts pass ([[adr-11-guardians]]).

## References

<!--
  ⛔ The most important section. Issue #189 was orphaned because it carried no
  reference graph a later agent could grep (see informe-sobre-issue-perdido.md).
  Link LIBERALLY. More links is always better than fewer. Use [[wikilinks]];
  point at code with repo-root-relative paths inside wikilinks.
-->

**Governing ADRs** — which decisions constrain this work
- [[adr-NN-slug]]

**Specs & docs** — the SSOTs this touches
- [[BDD]] · [[TDD]] · [[FRONTEND]] · [[BACKEND]] · [[API]] · [[DESIGN-SYSTEM]] · <trim to what applies>

**Code** — files/dirs the change lives in (repo-root-relative)
- [[frontend/src/lib/components/.../Thing.svelte]]
- [[backend/.../views.py]]

**Related work** — issues, PRs, handoffs, prior art
- #<issue> · #<pr>
- [[informe-sobre-issue-perdido]] <!-- or any handoff note -->

## Notes / out of scope

<!-- Anything a fresh agent must NOT assume. Environment gotchas, decisions deferred, etc. -->
