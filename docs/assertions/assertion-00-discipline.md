---
title: Assertion-00 — Assertion Discipline
description: Laws the project must pass — owner-reserved, proven by linked tests, driven through TDD into code
updated: 2026-08-02
---

## What an assertion is

An assertion is a **law** the project must pass — not a wish, not a backlog
item. It is a Gherkin use case collapsed into one paragraph, written
concretely enough that a skill can interpret every rule it imposes and
demand the tests that prove them.

> The user can get their last three messages, three clicks away from the home
> page, in a query, in less than 2 seconds.

That paragraph states the rules: what (the last three messages), how far
(three clicks from home), how (one query), how fast (under 2 seconds). An
assertion that cannot be checked is not an assertion.

**Assertions are the entry path for solutions.** The owner writes the law;
the `assertion-review` skill interprets it, demands proving tests via
[[TDD]], and that work prepares the fix or feature — above all the tests
that always verify the law. Tests first, code second; assertion, tests, and
code coexist in the project.

## Why they are few

Each assertion costs real compute: LLM interpretation, test authoring,
implementation, and periodic re-verification. They are **reserved for the
owner**. A project with none is healthy. Presence is what binds — every
assertion that exists must be met.

## Naming

```
assertion-NN-descriptive-slug.md
```

- `NN` is a two-digit, zero-padded number: `01`, `02`, …
- The slug is lowercase, hyphenated, no accents or special characters.
- `assertion-00` is reserved for this discipline.

## Format

The assertion paragraph comes first and states the rules. The file ends with
a `## RELATED` section: an open/close list, organized in `###` chapters,
linking everything that realizes or verifies the assertion — **tests first**,
then source files, docs, ADRs. Entries open and close as the project evolves;
the list is expected to churn even though the assertion itself stays put.

### Tests chapter is mandatory once work starts

At least one link under `### Tests` must point at a runnable test that
**demonstrates** the law. Example: *backend responds in 500ms or less*
requires a test that fails when latency exceeds 500ms. Until that link
exists and the test encodes the rules, the assertion is unmet — the
`assertion-review` skill must follow [[TDD]] rather than mark the law
verified.

## Review — the assertion-review skill

The skill at `docs/skills/assertion-review/SKILL.md` is how laws are
enforced and how solutions enter:

1. Read each assertion (or the one named in the dispatch).
2. Interpret with LLM judgment what the paragraph requires — every concrete
   rule, not a paraphrase of the title.
3. Resolve every `## RELATED` link; broken links fail the review.
4. Confirm `### Tests` proves the law. If not, **stop coding features** and
   execute [[TDD]]: demand failing tests, link them, then implement until
   green.
5. On success, set `verified` to today's date. On failure, leave `verified`
   as `never` or the last good date and report what is missing.

Assertions extend the base frontmatter convention
([CONVENTION.md](../constitution/CONVENTION.md)) with a `verified` key — the
date of the last successful review, or `never`.

## Alignment

Assertions are always aligned with [PRD.md](../constitution/PRD.md) and the
constitution. They are the constitution made verifiable: if an assertion
drifts from what the constitution says, the assertion is the one that is
wrong. The boundary with
[REQUIREMENTS.md](../constitution/REQUIREMENTS.md) is one of form:
requirements *enumerate* what must hold; an assertion takes one promise and
makes it a **law with a proving path** — concrete rules, linked tests,
[[TDD]], periodic review.

## Template

Copy this block as the starting point for a new assertion.

```markdown
---
title: Assertion-NN — [Short name]
description: [The promise, in one line]
verified: never
updated: YYYY-MM-DD
---

[The assertion: one paragraph stating what must be accomplished, with every
rule it imposes — concrete enough to be checked.]

## RELATED

### Tests

- [link to a runnable test that demonstrates this law]

### Files

- [link]

### Docs

- [link]
```
