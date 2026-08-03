---
title: adr-00-discipline
type: adr
category: harness
use_case: writing, editing, retiring or reviewing any ADR
created: 2026-07-10
modified: 2026-08-02
tags: [adr, discipline]
---

# ADR-00 — the ADR discipline

## CONTEXT

> Every ADR here has one shape and one theme, and outlives its own policies.
> This is that shape, and what happens when a decision changes.

## ASSERTIONS

1. An ADR states rules. Every fact, table, spec or explanation a rule stands
   on lives in a `docs/` document — the constitution included — and is
   reached by wikilink.
2. An ADR lives in `docs/adrs/`, named `adr-NN-slug.md` — sequential
   two-digit `NN`, kebab-case English slug. `adr-00` is reserved for this
   discipline.
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
   - `frontend` — the client surface (the interfaces side of the duality),
     including the design system;
   - `backend` — the server side (the services side), including APIs and
     databases;
   - `devops` — build, deploy, infrastructure, runtime;
   - `harness` — the agent tooling, and the rules and structure of the
     knowledge tiers themselves;
   - `project` — what stands outside the code: owners, roles, user stories,
     use cases.

   `use_case` states when this ADR must be consulted — the moment of work
   that triggers it, never the topic it covers. Name the acts a reader would
   recognise before opening the file: what is being built, which file is
   being touched, which decision is being made. More than one trigger is
   welcome, comma-separated, and it is always a single inline line — never a
   YAML list, never wrapped. Written as a topic it only repeats the title and
   the slot is wasted; written as a trigger, the frontmatter of all the ADRs
   read together becomes the index that says which few to open. For an ADR
   owning the API contract: `the API contract` is the topic and is wrong;
   `adding or changing an endpoint, editing docs/API.md, writing a
   serializer` is the trigger and is right.
4. An ADR has five level-2 sections, in this order:
   - `CONTEXT` — a single short quoted paragraph defining what this ADR is
     for. Up to two plain paragraphs may follow, and only when the quote
     alone leaves the reader unable to apply the rules. No links: they belong
     in `RELATED`;
   - `ASSERTIONS` — the numbered rules, each written as something the project
     does or requires;
   - `FORBIDDEN` — optional, written only when this ADR forbids something
     outright. Every entry opens with **NEVER** in bold, states the
     prohibited act as an imperative, names the rule it enforces, and ends
     with why. The heading is not the warning: a single entry is what gets
     quoted, grepped, pasted into an issue or read aloud by an agent, and it
     travels without the heading above it, so each line carries its own
     prohibition;
   - `REJECTED` — two things: the alternatives weighed and not taken, and
     every policy this ADR once held and holds no longer. Each entry gives
     the reason it lost and, where one exists, the condition that would
     reopen it. Nothing here is forbidden — it is what this project did not
     choose, or no longer chooses;
   - `RELATED` — every link the ADR carries, grouped under level-3 headings
     of the author's choosing.

   `FORBIDDEN` and `REJECTED` are omitted while empty. `REJECTED` rarely
   stays empty for long: it is where an ADR keeps its own history.
5. A rule is cited from anywhere as `adr-NN` rule `M`, so its number is
   permanent: a rule is appended, never renumbered.
6. Presence in `docs/adrs/` is what makes a rule binding: an ADR that is not
   in force is not there.
7. An ADR is attached to a theme and lives as long as that theme does. Its
   policy may change many times without the file ever moving: the theme is
   what the ADR is, the policy is only what it currently says. The whole file
   moves to `docs/obsolete/`, unchanged, only when the theme itself ends and
   the ADR governs nothing.
8. Changing a policy is done in place, and the policy being replaced moves
   into `REJECTED` in the same edit — so the body still reads as one current
   truth while the ADR keeps the record of what it used to require. A policy
   change is a decision and is made only with the owner's authorization,
   given in the conversation where it happens. A cosmetic edit — a typo, a
   format, a repaired wikilink, a clearer sentence — changes nothing else and
   needs no authorization. Every edit sets `modified` to that day.
9. Complying with every ADR in `docs/adrs/` is a precondition for adding
   anything to this project.
10. `docs/` content is reached through the vault (`markdown-vault-docs` MCP)
    before Grep or Read.
11. An ADR is the source of truth for the decision it records, and it
    outranks the code implementing it: where the two disagree, the ADR is
    right and the code is the defect. Authority runs [[PRD]] — the objective,
    then the rest of the constitution — how the project is run, then the
    ADRs — the decisions, then every other document, [[API]] included. Each
    of those still owns what it owns; each resolves beneath the ADR that
    governs it.

> [!note] This ADR is also its own template
> Rule 4 defines `FORBIDDEN` and `REJECTED`. The two sections below do not
> use them strictly — they demonstrate them, written for a reader learning
> the shape. Where the demonstration and rule 4 read differently, rule 4 is
> the usage.

## FORBIDDEN

- **NEVER** inline a fact in an ADR (rule 1). An ADR that carries its own
  facts becomes a second source of truth for them, and the two drift.
- **NEVER** state the same rule in two ADRs (rule 1). One ADR owns a rule;
  every other links to it.
- **NEVER** renumber a rule (rule 5). Citations elsewhere point at the
  number, and they are not all findable.
- **NEVER** drop a policy without recording it in `REJECTED` (rule 8). A
  rule that simply vanishes leaves the code that obeyed it looking wrong for
  a reason nobody can find again. Doubt about whether an edit changes policy
  resolves to recording it.
- **NEVER** leave a superseded policy standing beside the rule that replaced
  it (rule 8). The body is current truth; the history lives in `REJECTED`,
  never in the assertions.
- **NEVER** resurrect a body out of `docs/obsolete/` (rule 7). A theme that
  ended is written new if it returns; the old body carries the context of a
  project that no longer exists.

## REJECTED

- **A `status` field in frontmatter** — `proposed | accepted | deprecated |
  superseded` (this project's own prior shape used `active | defered`) on
  every ADR, the shape this discipline used until 2026-08-02. Dropped
  because the directory already answers the question, and a second answer
  can disagree with the first. It would reopen only if an ADR ever needed to
  sit in `docs/adrs/` without binding; no such need is known.
- **An immutable body with supersession chains** — the policy this
  discipline held until 2026-08-02: once accepted, an ADR's body froze, and
  every change of mind spawned a successor that superseded it. It kept each
  file immutable, but it scattered one theme across a chain of numbers, so
  the current answer could only be found by walking the chain, and the ADR
  count grew with the project's mind changing rather than with its concerns.
  Replaced by rule 7 — the theme holds the number, the policy moves through
  `REJECTED`. It would reopen only if an ADR's history grew long enough to
  bury its current rules, which is a reason to split the theme, not to
  retire the file.
- **Leaving a hollow stub behind on retirement** — the retired file staying
  in place with its frontmatter and an empty body. It keeps the number
  visible where it had always been, but under rule 6 a file present in
  `docs/adrs/` reads as in force, and a hollow one would read as a rule with
  no content. Closed for as long as rule 6 stands.
- **This project's own former numbering (2026-07-10 to 2026-08-02)** — this
  repository's ADRs 00 (this discipline), 01 (glossary and localization), 02
  (initial stack), 03 (API and backend), 04 (frontend and design system), 11
  (guardians) and 14 (harness) held the numbers 00–04, 11 and 14 under the
  same discipline described above, word-for-word compatible with it. On
  2026-08-02, in the conversation adopting the `kodexArg/harness-default`
  doctrine wholesale, the owner authorized breaking rule 5 (permanent rule
  numbers) and rule 7 (a theme holds its number for life) for this one
  migration only: 01→12, 02→50, 03→51, 04→52 were renumbered by filename
  though every rule inside each file kept its own original number, and 11
  and 14 were folded — their surviving content appended, never renumbered,
  as new rules onto [[adr-03-guardians]] and [[adr-02-harness]]
  respectively. This is a one-time exception recorded here per rule 8; it
  authorizes nothing beyond this migration, and no ADR may cite it to justify
  a future renumbering or theme move.

## RELATED

### governed paths

- `docs/adrs/` — every ADR, all in force
- `docs/obsolete/` — every retired ADR, whole and inert

### related files

- [[adr-01-constitution]] — first project-law ADR beneath this discipline
- [[HARNESS]] — how the harness fits together; names this family and its
  discipline
- [[CONVENTION]] — the base frontmatter convention that this family's seven
  fields replace
- [[PRD]] — the top of the authority order in rule 11
</content>
