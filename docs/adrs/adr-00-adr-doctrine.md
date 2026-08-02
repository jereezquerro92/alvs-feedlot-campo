---
title: adr-00-adr-doctrine
type: adr
category: harness
use_case: writing, editing, superseding or reviewing any ADR
created: 2026-07-10
modified: 2026-08-02
tags: [adr, doctrine]
---

# ADR-00 — the ADR doctrine

## CONTEXT

> Every ADR here has one shape and one theme, and outlives its own policies. This is that shape, and what happens when a decision changes.

## ASSERTIONS

1. An ADR states rules. Every fact, table, spec or explanation a rule stands on lives in a `docs/` document and is reached by wikilink.
2. An ADR lives in `docs/adrs/`, named `adr-NN-slug.md` — sequential `NN`, kebab-case English slug.
3. Frontmatter carries exactly these seven fields, in this order:

   | field | value |
   |---|---|
   | `title` | the filename without `.md` — `adr-NN-slug` |
   | `type` | always `adr` |
   | `category` | one of the five below |
   | `use_case` | when to consult this ADR — see below |
   | `created` | `YYYY-MM-DD`, the day the ADR was first written; never changes again |
   | `modified` | `YYYY-MM-DD`, the day of its last edit (rule 8) |
   | `tags` | inline list for retrieval, lowercase, `adr` first |

   `category` is one of:
   - `frontend` — the client surface, including the design system;
   - `backend` — the server, including the API and the database;
   - `devops` — build, deploy, infrastructure, runtime;
   - `harness` — the agent tooling, and the rules and structure of `docs/` itself;
   - `project` — what stands outside the code: owners, roles, user stories, use cases.

   `use_case` states when this ADR must be consulted — the moment of work that triggers it, never the topic it covers. Name the acts a reader would recognise before opening the file: what is being built, which file is being touched, which decision is being made. More than one trigger is welcome, comma-separated, and it is always a single inline line — never a YAML list, never wrapped. Written as a topic it only repeats the title and the slot is wasted; written as a trigger, the frontmatter of all the ADRs read together becomes the index that says which few to open. For an ADR owning the API contract: `the API contract` is the topic and is wrong; `adding or changing an endpoint, editing docs/API.md, writing a serializer` is the trigger and is right.
4. An ADR has five level-2 sections, in this order:
   - `CONTEXT` — a single short quoted paragraph defining what this ADR is for. Up to two plain paragraphs may follow, and only when the quote alone leaves the reader unable to apply the rules. No links: they belong in `RELATED`;
   - `ASSERTIONS` — the numbered rules, each written as something the project does or requires;
   - `FORBIDDEN` — optional, written only when this ADR forbids something outright. Each entry names the rule it enforces;
   - `REJECTED` — two things: the alternatives weighed and not taken, and every policy this ADR once held and holds no longer. Each entry gives the reason it lost and, where one exists, the condition that would reopen it. Nothing here is forbidden — it is what this project did not choose, or no longer chooses;
   - `RELATED` — every link the ADR carries, grouped under level-3 headings of the author's choosing.

   `FORBIDDEN` and `REJECTED` are omitted while empty. `REJECTED` rarely stays empty for long: it is where an ADR keeps its own history.
5. A rule is cited from anywhere as `adr-NN` rule `M`, so its number is permanent: a rule is appended, never renumbered.
6. Presence in `docs/adrs/` is what makes a rule binding. There is no status field, because an ADR that is not in force is not there.
7. An ADR is attached to a theme and lives as long as that theme does. Its policy may change many times without the file ever moving: the theme is what the ADR is, the policy is only what it currently says. The whole file moves to `docs/obsolete/`, unchanged, only when the theme itself ends and the ADR governs nothing.
8. Changing a policy is done in place, and the policy being replaced moves into `REJECTED` in the same edit — so the body still reads as one current truth while the ADR keeps the record of what it used to require. A policy change is a decision and is made only with the owner's authorization, given in the conversation where it happens. A cosmetic edit — a typo, a format, a repaired wikilink, a clearer sentence — changes nothing else and needs no authorization. Every edit sets `modified` to that day.
9. Complying with every ADR in `docs/adrs/` is a precondition for adding anything to this project.
10. `docs/` content is reached through the `markdown-vault-docs` MCP before Grep or Read.
11. An ADR is the source of truth for the decision it records, and it outranks the code implementing it: where the two disagree, the ADR is right and the code is the defect. Authority runs [[PRD]] — the objective, then [[AGENTS]] — how work is done, then the ADRs — the decisions, then every other document, [[API]] included. Each of those still owns what it owns; each resolves beneath the ADR that governs it.

> [!note] This ADR is also its own template
> Rule 4 defines `FORBIDDEN` and `REJECTED`. The two sections below do not use them strictly — they demonstrate them, written for a reader learning the shape. Where the demonstration and rule 4 read differently, rule 4 is the usage.

## FORBIDDEN

- **Inlining a fact in an ADR** (rule 1). An ADR that carries its own facts becomes a second source of truth for them, and the two drift.
- **Stating the same rule in two ADRs** (rule 1). One ADR owns a rule; every other links to it.
- **Renumbering a rule** (rule 5). Citations elsewhere point at the number, and they are not all findable.
- **Dropping a policy without recording it in `REJECTED`** (rule 8). A rule that simply vanishes leaves the code that obeyed it looking wrong for a reason nobody can find again. Doubt about whether an edit changes policy resolves to recording it.
- **Leaving a superseded policy standing beside the rule that replaced it** (rule 8). The body is current truth; the history lives in `REJECTED`, never in the assertions.
- **Resurrecting a body out of `docs/obsolete/`** (rule 7). A theme that ended is written new if it returns; the old body carries the context of a project that no longer exists.

## REJECTED

- **A `status` field in frontmatter** — `active | defered` on every ADR, the shape this doctrine used until 2026-08-02. Dropped because the directory already answers the question, and a second answer can disagree with the first. It would reopen only if an ADR ever needed to sit in `docs/adrs/` without binding; no such need is known.
- **Leaving a hollow stub behind on supersession** — the superseded file staying in place with its frontmatter and an empty body. It kept the number visible where it had always been, but under rule 6 a file present in `docs/adrs/` reads as in force, and a hollow one would read as a rule with no content. Closed for as long as rule 6 stands.
- **Retiring the whole ADR on any policy change** — the policy this doctrine held until 2026-08-02: every change to what a rule required sent the file to `docs/obsolete/` and spawned a successor ADR. It kept each file immutable, but it scattered one theme across a chain of numbers, so the current answer could only be found by walking the chain, and the ADR count grew with the project's mind changing rather than with its concerns. Replaced by rule 7 — the theme holds the number, the policy moves through `REJECTED`. It would reopen only if an ADR's history grew long enough to bury its current rules, which is a reason to split the theme, not to retire the file.

## RELATED

### related adrs

- [[docs/adrs/adr-01-glossary-and-localization]] — names and language, decided before first use
- [[docs/adrs/adr-18-markdown-vault-mcp]] — the MCP that rule 10 mandates

### governed paths

- `docs/adrs/` — every ADR, all in force
- `docs/obsolete/` — every superseded ADR, whole and inert
- `.claude/rules` — the symlink through which the harness loads the rule set

### related files

- [[AGENTS]] — the gate that checks rule 9 before anything is added
- [[docs/GLOSSARY]] — a name is decided there before its first use
- [[docs/LOCALIZATION]] — everything written is English
