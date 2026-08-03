---
title: adr-18-markdown-vault-mcp
type: adr
category: harness
use_case: searching or reading anything under docs/, traversing the wikilink graph, editing a doc and needing the index fresh, bootstrapping the MCP on a fresh clone
created: 2026-07-14
modified: 2026-08-02
tags: [adr, harness, mcp, docs]
---

# ADR-18 — the vendored markdown-vault MCP

## CONTEXT

> The `docs/` vault is reached through its own MCP server, vendored with the repo. This ADR gives that server its force; the server itself, its config and its tools are described elsewhere.

## ASSERTIONS

1. The markdown-vault MCP (`markdown-vault-docs`) is the first source of truth for reaching `docs/` content — searching, reading, and traversing the vault graph. An agent consults it before Grep or Read for any `docs/` prose or wikilink question ([[adr-00-discipline]] rule 10). Grep and Read stay free for code, configs and everything outside `docs/`.
2. The server is vendored and travels with the repo, never registered machine-globally: a project-scoped `.mcp.json`, a self-bootstrapping launcher `scripts/mvmcp.py`, and a git-ignored `.mvmcp/` holding the project-local venv, index and embeddings. A fresh clone exposes it with no external link — the discipline [[adr-02-harness]] imposes on skills, applied to the MCP. Its inventory row lives in [[SKILL-INVENTORY]] and its version pin in [[REQUIREMENTS]].
3. The server name is `markdown-vault-docs` and its env stem is `MARKDOWN_VAULT_MCP_`, both registered in [[GLOSSARY]] before use. That env is harness tooling — never app runtime, never a secret — so it does not enter [[VARIABLES]], which governs only what backend or frontend code reads ([[adr-51-api-and-backend]] rule 7).
4. This MCP owns the `docs/` prose and wikilink graph; `codebase-memory-mcp` owns the code graph. Neither is folded into the other: a code-structure question goes to codebase-memory first, a doc question here.
5. The index is kept fresh. After `docs/` changes it is rebuilt or reindexed before its answers are trusted; the `mvmcp_freshness.py` SessionStart hook is the safety net, not the trigger. Writes carry the link-index degradation caveat recorded in [[markdown-vault-mcp]], and Obsidian syntax is still authored through the `obsidian-markdown` skill ([[SKILL-INVENTORY]]).
6. This ADR gives force and states no procedure. The bootstrap, the tool list, the exclusion set and the indexed frontmatter fields are owned by [[markdown-vault-mcp]] ([[adr-00-discipline]] rule 1).

## FORBIDDEN

- **NEVER** answer a `docs/` prose or wikilink question from Grep or Read before the MCP (rule 1). The vault graph is what holds the answer, and grep cannot see it.
- **NEVER** register this server machine-globally or depend on a machine-global copy (rule 2). A clone that needs an external link is a clone that does not work.
- **NEVER** trust the MCP's answers after editing `docs/` without a reindex (rule 5). A stale index answers confidently with the previous truth.
- **NEVER** put a procedure in this ADR (rule 6). It lives in [[markdown-vault-mcp]], which is the document the tooling follows.

## REJECTED

- **Registering the MCP in the machine-global harness** — one installation shared by every project on the host. Rejected for the same reason vendored skills were: it makes the repo depend on the machine it was cloned onto, and the dependency is invisible until it breaks.
- **Folding the doc graph into `codebase-memory-mcp`** — one server answering both code and prose. Rejected because the two graphs are built from different things and merging them makes each answer worse; rule 4 keeps them apart.

## RELATED

### related adrs

- [[docs/adrs/adr-00-discipline]] — rule 10, the MCP-first order this ADR carries out
- [[docs/adrs/adr-02-harness]] — the vendoring discipline rule 2 follows
- [[docs/adrs/adr-51-api-and-backend]] — rule 7, why the launcher's env stays out of [[VARIABLES]]

### related files

- [[docs/markdown-vault-mcp]] — the server, its config, tools and caveats
- [[docs/SKILL-INVENTORY]] — the inventory row and the `obsidian-markdown` skill
- [[docs/GLOSSARY]] — the server name and env stem
- [[docs/constitution/REQUIREMENTS]] — the version pin
