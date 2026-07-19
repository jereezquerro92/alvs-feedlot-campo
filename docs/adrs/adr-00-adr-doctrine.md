---
title: adr-00-adr-doctrine
type: adr
status: active
created: 2026-07-10
tags: [adr, doctrine]
---

# ADR-00 — the ADR doctrine

Rules only; content lives in the linked docs.

1. An ADR states rules, never information. Facts, tables, specs and explanations live in `docs/` and are reached by wikilink. If an ADR needs a fact, it links the doc that owns it — it never inlines it.
2. ADRs live in `docs/adrs/`, inside the vault the markdown-vault MCP serves ([[adr-18-markdown-vault-mcp]]); `.claude/rules/` is the same directory through a link, so the agent harness loads them as rules. Naming: `adr-NN-slug.md` — sequential `NN`, kebab-case English slug ([[GLOSSARY]], [[LOCALIZATION]]).
3. Frontmatter: `title`, `type: adr`, `status: active | defered`, `created`, `tags`.
4. Supersession. Any change that alters, narrows, widens, or reverses the force of a rule — what it requires or forbids — is semantic and MUST supersede:
   - its full body moves to `docs/obsolete/defered-adr-NN-slug.md`;
   - the original keeps ONLY its frontmatter, set `status: defered`, body empty;
   - the replacement rule, if any, is written as a new ADR.
   A defered ADR therefore contributes zero content to any context. Never resurrect a body — write a new ADR.
   In-place edition without supersession is permitted ONLY for: (a) cosmetic, non-semantic changes — typos, formatting, wikilink repair, wording clarification that leaves what the rule requires or forbids unchanged; (b) a change made under the owner's express consent given in the current conversation. Either path MUST NOT leave negated or historical content standing — the body always reads as current truth. Doubt about whether a change is semantic resolves to supersede.
5. Compliance with active ADRs is a precondition for adding anything; the ABC gate is defined in [[AGENTS]].
6. The sanctioned interface for reaching the docs this doctrine points to is the markdown-vault MCP. An ADR resolves its facts by wikilink (rule 1); the tool that searches, reads, and traverses those `docs/` targets is the `markdown-vault-docs` MCP — the first source of truth for `docs/` content, consulted before Grep/Read ([[adr-18-markdown-vault-mcp]], [[markdown-vault-mcp]]).
