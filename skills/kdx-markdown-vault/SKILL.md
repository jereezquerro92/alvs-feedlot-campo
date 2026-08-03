---
name: kdx-markdown-vault
description: Drive the markdown-vault-docs MCP — the first source of truth for docs/ content in the astro-drf-aws template. Use for any question about docs/ prose or its wikilink graph (search, read, backlinks, similarity), before Grep/Read. Also covers bootstrap, reindex, and the write caveat. Ruled by adr-18-markdown-vault-mcp; full config in docs/markdown-vault-mcp.md.
---

# kdx-markdown-vault — query the docs/ vault graph

The `markdown-vault-docs` MCP indexes `docs/` (this template's Obsidian vault) as a
searchable, backlink-aware, semantically-indexed graph. It is the **first source of
truth for `docs/` content** — query it before Grep/Read for any `docs/` prose or
wikilink question. Grep/Read stay correct for code, configs, and non-`docs/` files;
code structure goes to `codebase-memory-mcp` first. Force: [[adr-18-markdown-vault-mcp]].
Config SSOT: [[markdown-vault-mcp]].

## When to reach for it

- "Where is X documented?" / "which doc owns this rule?" → `search` (`mode='hybrid'`).
- "What links to [[API]]?" / "what does this doc reference?" → `get_backlinks` / `get_outlinks`.
- "What's related to this note?" → `get_similar` (semantic).
- "Show me the full doc" → `read` / `fetch` by relative path (e.g. `adrs/adr-10-auth.md`).
- Graph hygiene → `get_orphan_notes`, `get_broken_links`.

## Tool cheat-sheet

| Need | Tool |
|---|---|
| find documents | `search` — prefer `mode='hybrid'`; filter by `folder` / frontmatter fields |
| open a document | `read` / `fetch` (relative path) |
| traverse links | `get_backlinks`, `get_outlinks`, `get_connection_path` |
| find related | `get_similar`, `get_context` |
| enumerate | `list_documents`, `list_folders`, `list_tags`, `get_recent`, `get_most_linked` |
| hygiene | `get_orphan_notes`, `get_broken_links`, `stats` |
| write | `write` (create), `edit` (read first), `rename` (`update_links=True`), `delete` |

`browse_vault` / `show_context` open a visual UI for the human — never call them to
retrieve content.

## Bootstrap & freshness

The index is git-ignored (`.mvmcp/`), so each clone builds its own:

```
python3 scripts/mvmcp.py bootstrap    # venv + index + embeddings
```

After editing `docs/`, refresh before trusting the vault: call the `reindex` tool or
re-run `bootstrap`. The `mvmcp_freshness.py` SessionStart hook warns when stale.

> [!warning] Write degrades the link index
> Heavy `write`/`edit`/`rename`/`delete` can degrade the backlink index over time; after
> a batch of writes run `reindex`, and treat `get_backlinks` as authoritative only after.
> Prose is still authored through the `obsidian-markdown` skill — this MCP finds and reads,
> `obsidian-markdown` writes correct Obsidian syntax ([[markdown-vault-mcp]]).
