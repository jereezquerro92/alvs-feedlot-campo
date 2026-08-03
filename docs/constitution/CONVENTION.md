---
title: Convention
description: Global conventions that apply to every document in this harness
updated: 2026-08-02
---

## Frontmatter documentation

Every markdown document under `docs/` — and the root `README.md` — opens
with a YAML frontmatter block. It is the machine-readable summary of the
document: agents read it to decide whether the file is worth opening, and
tooling can index it without parsing prose.

Tooling files are exempt: `docs/skills/`, `docs/hooks/`, and `docs/agents/`
obey the formats their tools fix (a skill's `SKILL.md` carries `name` +
`description`), not this convention.

Required keys:

| Key | Value |
|---|---|
| `title` | Short human-readable title. |
| `description` | One line stating what the document contains and when to read it. |
| `updated` | Date of last meaningful edit, `YYYY-MM-DD`. |

Rules:

- Frontmatter is the first thing in the file: `---` on line 1.
- Keys are lowercase and flat (no nesting); values are plain YAML scalars.
- `description` fits in one line (< 160 chars) — it is the hook an agent uses
  to decide relevance without opening the body.
- A document that is present is valid — validity lives in the tree, not in
  an annotation. Information that stops being true is removed: deleted,
  retired whole to `docs/obsolete/`, or recorded as displaced policy inside
  the owning ADR — `REJECTED`, or `FORBIDDEN` when the old way is now
  prohibited.
- Document families may extend the base set with their own keys — assertions
  add `verified` — or their discipline file may own the frontmatter outright:
  ADRs carry exactly seven fields of their own, and presence in `docs/adrs/`
  is what makes an ADR binding. See
  [adr-00-discipline](../adrs/adr-00-discipline.md) and
  [assertion-00-discipline](../assertions/assertion-00-discipline.md).
