---
title: Harness
description: What this harness is, how its pieces fit together, and how to work inside it
updated: 2026-08-02
---

This harness is the doctrine layer of alvs-feedlot-campo. Everything the
project **knows** lives under `docs/` — the constitution, the loose
documents, the ADR and assertion families, and even the agent tooling.
Outside `docs/` there is only what the project **is**: `backend/`,
`frontend/` and their runtime state. The written knowledge is served as a
wikilink-aware vault by the vendored `markdown-vault-docs` MCP
([[adr-18-markdown-vault-mcp]]) — see [The vault](#the-vault) below.

> [!note] Where the vendored skill inventory moved
> This file used to also carry the project's vendored-skill inventory (why
> each `kdx-*` skill is required, and its consumers). That table now lives
> in [[SKILL-INVENTORY]], loose under `docs/`, unaffected by this doctrine
> reshuffle.

## Tiers and families

Written knowledge comes in two kinds of containers inside `docs/`.
`docs/constitution/` and the documents sitting directly in `docs/` are
**tiers**: every document sorts into one of them by a single question — **is
this both meaningful and stable?** `docs/adrs/` and `docs/assertions/` are
**families**: numbered, append-only files that do not sort — they
accumulate, each ruled by its own `-00` discipline file.

### docs/constitution/

The constitution holds what the project does not expect to change. These
documents are foundational and binding: they are read first, they settle
arguments, and they are amended rarely and deliberately. Changing the
constitution is an event, not routine upkeep.

A document earns its place here only by being both things at once —
meaningful *and* stable. Meaningful but volatile belongs one level up,
directly in `docs/`; stable but unimportant belongs there too.

### docs/ — the loose documents

Everything else sits directly in `docs/`, which covers two kinds of
material:

- **Documents that iterate with the code.** `API.md` is the clearest case:
  the surface it describes moves constantly, and the document is expected
  to move with it.
- **Documentation that is stable but not load-bearing.** Useful reference,
  kept current, but a change to it would not alter how the project is run.

### How this project's constitution-tier files sort

| File | Why |
|---|---|
| `PRD.md` | The objective and the horizon — always in memory, changes only by owner decision. |
| `REQUIREMENTS.md` | Exact version pins for the stack — set deliberately, re-verified, not iterated casually. |
| `HARNESS.md` | This file — the doctrine explainer, meaningful and stable by construction. |
| `CONVENTION.md` | The frontmatter contract every `docs/` file opens with — foundational, rarely amended. |
| `LOCALIZATION.md` | Language and locale policy — decided once, binds every later use. |
| `INFRASTRUCTURE.md` | The bare metal beneath the project — cloud choice, resources, set up once, barely varies. |

Everything else this project already holds under `docs/` — `API.md`,
`ARCHITECTURE.md` (not yet created), `BACKEND.md`, `FRONTEND.md`,
`GLOSSARY.md`, `TDD.md`, `SKILL-INVENTORY.md`, the feedlot domain
documents, and the rest — iterates with the code or is stable-but-not-
load-bearing, and stays loose. See [[CODEMAP]] for the doc→code inverse
index and each individual ADR's `RELATED` section for what governs what.

## docs/adrs/

Architecture Decision Records: the memory of the why, not just the what. An
ADR is attached to a *theme* and states numbered rules; its policy may
change many times in place — each displaced policy recorded in the ADR's
own `REJECTED` section — without the file ever moving. Presence in
`docs/adrs/` is what makes a rule binding, and a whole file retires to
`docs/obsolete/` only when its theme ends. Discipline and template:
[[adr-00-discipline]]. This project's ADR set is large (49+ files); the
standing order of the four harness-doctrine ADRs specifically is:

| ADR | Theme |
|---|---|
| [[adr-00-discipline]] | The ADR discipline itself — shape, lifecycle, authority order |
| [[adr-01-constitution]] | Source markdown — PRD, constitution, families, authority |
| [[adr-02-harness]] | Skills, hooks, agents — tooling that serves the law |
| [[adr-03-guardians]] | Guardian agents and the dispatch safety net |

Every other ADR in `docs/adrs/` governs this project's own domain and
stack decisions; see [[GLOSSARY]] and each file's own `RELATED` section.

## docs/assertions/

Assertions are the harness's **novel piece**: owner-reserved **laws** that
a skill must pass. Everything else in this tree is ordinary scaffolding
plus a written PRD and ADRs-as-rules; assertions are the entry path for
solutions that manifest first as proving tests ([[TDD]]) and then as code.

The family is completely optional — a project with none is healthy. They
stay few because each one costs real compute (interpret, demand tests,
implement, re-verify). Presence is what binds — every assertion that
exists must be met. Discipline and template: [[assertion-00-discipline]].
This migration seeds only the discipline file; no product assertion is
invented without the owner.

## Code roots

This project already committed to the specific pair: `backend/` +
`frontend/` ([[adr-09-docker-compose]] rule 1). The generalistic pair
(`interfaces/` + `services/`) was never adopted and is out of scope here.

## Agent tooling

- **skills** — instruction packages an agent loads on demand. This
  project's inventory (why each is required, and its consumers) lives in
  [[SKILL-INVENTORY]], vendored under `.claude/skills/` and mirrored at
  `skills/` ([[adr-02-harness]]).
- **hooks** — automation attached to agent or git lifecycle events.
  `.claude/hooks/dispatch_guardians.py` is this project's `PostToolUse`
  dispatch safety net ([[adr-03-guardians]]).
- **agents** — role definitions. This project's three
  `astro-drf-aws-{prd,adr,api}` guardians gate the PRD, the ADR set and
  [[API]] respectively ([[adr-03-guardians]]).

Tooling lives under `docs/` or its git-tracked mirrors with the knowledge
it belongs to, but the vault excludes tooling folders: tooling conventions
fix their filenames, which would collide with the vault's naming rule
below.

## The vault

The vault root is `docs/`: everything documental is indexed, except the
tooling folders. It is served by the vendored `markdown-vault-docs` MCP
([[adr-18-markdown-vault-mcp]], [[markdown-vault-mcp]]) — project-scoped,
self-bootstrapping, no machine-global dependency.

Working rules:

- **Query the vault first** for any documentation question — search, read,
  backlinks, similarity — before grepping the markdown by hand
  ([[adr-00-discipline]] rule 10).
- **Basenames are unique vault-wide.** A wikilink resolves by basename;
  duplicates make it resolve to the wrong file.
- **Wikilinks are welcome** between notes: `[[adr-00-discipline]]`,
  `[[HARNESS]]`. The vault tracks them as a graph — backlinks, orphans,
  broken links are all queryable.
- **Reindex after a batch of edits** before trusting link queries again.
