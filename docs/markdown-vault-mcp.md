---
title: markdown-vault-mcp
type: reference
status: active
created: 2026-07-14
tags: [harness, mcp, docs, ssot]
---

# markdown-vault-mcp — the docs/ vault as a live, queryable graph

The content SSOT for the vendored **markdown-vault MCP**. Its force is [[adr-18-markdown-vault-mcp]]; this file owns everything that ADR only points to. The server turns `docs/` — this template's Obsidian vault — into a searchable, backlink-aware, semantically-indexed graph, and it is the **mandatory first source of truth for reaching `docs/` content** ([[adr-18-markdown-vault-mcp]] rule 1, [[AGENTS]]).

> [!important] First, not optional
> For any question about `docs/` prose or its wikilink structure, query the `markdown-vault-docs` MCP **before** Grep/Read: `search` to find, `read` to open, `get_backlinks`/`get_outlinks`/`get_similar` to traverse. Grep/Read stay correct for code, configs, and non-`docs/` files. This mirrors how `codebase-memory-mcp` is the first source for code ([[HARNESS]]).

## Why it is here (and why vendored)

The harness at the heart of this product is its documentation graph ([[PRD]]): a web of SSOTs joined by `[[wikilinks]]`, guarded by ADRs. Reading that graph by grepping filenames throws away the graph. The MCP restores it — link-following, similarity, orphan/broken-link detection — as tools. It is **vendored and transported with the repo**, not registered per-machine, so a fresh clone on any machine has it with no external setup — the same self-contained rule [[adr-14-harness]] imposes on skills ([[adr-18-markdown-vault-mcp]] rule 2).

## The moving parts

| Piece | Path | Committed? | Role |
|---|---|---|---|
| Project MCP config | `.mcp.json` | yes | Declares the `markdown-vault-docs` server; Claude auto-detects and prompts to approve it on clone. |
| Launcher / bootstrap | `scripts/mvmcp.py` | yes | Self-bootstraps the venv, assembles env, `exec`s the server on stdio. No absolute paths — path-independent. Picks the profile (see below). |
| Cloud setup script | `scripts/cloud_setup.sh` | yes | Pre-warms the MCP in a cloud environment, and best-effort bakes the frontend's bun dependencies (`node_modules`) into the snapshot; pasted as one line into the environment's Setup script field. |
| Freshness hook | `.claude/hooks/mvmcp_freshness.py` | yes | SessionStart: warns when the index is stale or missing. Safety net, not the trigger. |
| Version pin | [[REQUIREMENTS]] | yes | `markdown-vault-mcp[embeddings]` pin; policy owned there. |
| venv + index + embeddings | `.mvmcp/` | **no** (git-ignored) | Build artifact: project-local venv, `data/index.db`, `data/embeddings`, `data/state.json`. Machine-specific, rebuildable. |

The server name is **`markdown-vault-docs`** and the env stem is **`MARKDOWN_VAULT_MCP_`** — both registered in [[GLOSSARY]].

## Configuration

`scripts/mvmcp.py` sets these; they are **harness-dev tooling, not app runtime and never secrets**, so they do **not** enter [[VARIABLES]] ([[adr-18-markdown-vault-mcp]] rule 3):

| Env var | Value | Purpose |
|---|---|---|
| `MARKDOWN_VAULT_MCP_SOURCE_DIR` | `./docs` | The vault root. |
| `MARKDOWN_VAULT_MCP_READ_ONLY` | `false` | Write tools enabled. |
| `MARKDOWN_VAULT_MCP_INDEX_PATH` | `.mvmcp/data/index.db` | SQLite full-text index. |
| `MARKDOWN_VAULT_MCP_EMBEDDINGS_PATH` | `.mvmcp/data/embeddings` | Vector store for semantic search. |
| `MARKDOWN_VAULT_MCP_STATE_PATH` | `.mvmcp/data/state.json` | Incremental-index state. |
| `MARKDOWN_VAULT_MCP_EMBEDDING_PROVIDER` | `fastembed` | Local embeddings — **no API key, no external service, no secret**. |
| `MARKDOWN_VAULT_MCP_FASTEMBED_MODEL` | `BAAI/bge-small-en-v1.5` | Small English model (~130 MB, downloaded once on first build). |
| `MARKDOWN_VAULT_MCP_EXCLUDE` | `.obsidian/**,.vscode/**` | Non-content paths. |
| `MARKDOWN_VAULT_MCP_INDEXED_FIELDS` | `title,type,status,tags,created` | This vault's frontmatter fields, filterable in `search`. |

The three embedding rows above belong to the **full** profile only — see below.

## The two profiles — full and keyword

Semantic search needs a model the launcher cannot always reach: `fastembed` fetches `BAAI/bge-small-en-v1.5` from `huggingface.co`, which is **not** on the Claude Code cloud sandbox's default Trusted allowlist (PyPI is). This is not a graceful loss. The server treats an *explicitly pinned* provider it cannot load as a fatal configuration error, by design — so pinning `fastembed` where the model is unreachable does not fall back to keyword search, it stops the MCP from starting at all. Unsetting the provider does not help either: auto-detection finds the installed `fastembed` and dies the same way. Only *not installing the extra* degrades cleanly.

Hence two profiles, chosen by `scripts/mvmcp.py`:

| | **full** | **keyword** |
|---|---|---|
| Default where | local (kodex's machines) | cloud (`CLAUDE_CODE_REMOTE=true`) |
| Pin | `markdown-vault-mcp[embeddings]` | `markdown-vault-mcp` |
| Provider pinned | `fastembed` | none — no provider, no embeddings path |
| venv | ~245 MB | ~65 MB |
| Needs `huggingface.co` | yes | no |
| `search` · `read` · `get_backlinks` · `get_outlinks` | ✔ | ✔ — these rest on the FTS index and the link graph, not vectors |
| `get_similar` · semantic `search` | ✔ | ✘ |

`MARKDOWN_VAULT_MCP_PROFILE` (`full` / `keyword`) overrides the default in either direction; an unrecognised value is logged and ignored rather than served as a guess. The launcher stamps the installed profile at `.mvmcp/profile` and reinstalls when it changes, so a venv built for one profile is never served as the other.

**Full parity in the cloud** is opt-in and costs one piece of config this repo cannot carry: set the environment's network access to **Custom**, add `huggingface.co` to its allowed domains, and set `MARKDOWN_VAULT_MCP_PROFILE=full` in the same environment. Without that, the keyword profile is the correct choice — a live MCP with keyword search beats a dead one with semantic search.

The keyword profile's `bootstrap` prints an `Embeddings require both 'embedding_provider' and 'embeddings_path'` ValueError. It is expected and non-fatal: the server reports the vector step it skipped and carries on. Exit 0 and an `index.db` under `.mvmcp/data/` are the success signal.

## Cloud sessions

A cloud session clones the repo and gets `.mcp.json`, `scripts/mvmcp.py` and the hooks — but never `.mvmcp/`, which is git-ignored and machine-specific. It rebuilds. Paste one line into the environment's **Setup script** field:

```
bash scripts/cloud_setup.sh
```

Everything that script does stays versioned in the repo. It runs once per environment, before Claude Code launches, and Anthropic snapshots the filesystem afterwards — so later sessions start with the venv and index already on disk instead of paying for them. A `SessionStart` hook would run on *every* session including resumes, which is why the install lives in the setup script and not there.

Note that `codebase-memory` takes the opposite route: it stays local-only and is absent from cloud sessions entirely ([[HARNESS]]). The two MCPs are disjoint and so are their answers to the cloud ([[adr-18-markdown-vault-mcp]] rule 4).

## Bootstrap & freshness

```
python3 scripts/mvmcp.py bootstrap    # create venv, install pin, build index + embeddings
python3 scripts/mvmcp.py serve        # what .mcp.json runs; bootstraps if needed, serves on stdio
```

The index is **not** committed — every clone builds its own on first `bootstrap` or first `serve`. After editing `docs/`, refresh before trusting the vault: call the `reindex` tool, or re-run `bootstrap`. The `mvmcp_freshness.py` SessionStart hook compares the newest `docs/*.md` mtime against `index.db` and nudges when stale or missing.

> [!warning] Write degrades the link index
> A known behaviour ([[adr-18-markdown-vault-mcp]] rule 5): heavy `write`/`edit`/`rename`/`delete` through the MCP can degrade the backlink index over time. Single edits update the index immediately; after a batch of writes, run `reindex` (or `bootstrap`) and treat `get_backlinks` as authoritative only post-refresh. Prose and Obsidian syntax are still authored through the `obsidian-markdown` skill ([[HARNESS]]).

## Tool cheat-sheet

Read/traverse (the common path):

- `search` — find documents; prefer `mode='hybrid'` (full-text + semantic) when available.
- `read` / `fetch` — full content of a note by relative path.
- `get_backlinks` / `get_outlinks` — the wikilink edges into/out of a note.
- `get_similar` — semantically nearest notes (embeddings).
- `get_context` / `get_connection_path` — neighbourhood, or the link path between two notes.
- `list_documents` / `list_folders` / `list_tags` / `get_recent` / `get_most_linked` — enumerate.
- `get_orphan_notes` / `get_broken_links` — graph hygiene.
- `stats` — capabilities and index status.

Write (honour the caveat above): `write` (create), `edit` (targeted change — read first), `rename` (`update_links=True` to fix inbound links), `delete`.

> [!note] `browse_vault` / `show_context` open a visual UI for the human — do not call them to retrieve content; use `search`/`read`/`get_context`.

## Keeping code linked to the vault — the live-doc docstring convention

The vault indexes `docs/`; code files reach into it through their **live-doc block** — a wikilinks-only region at the top of every governed code file, naming the ADRs and docs that rule it. That is what keeps documentation *live*: a `.py` or `.astro` file carries, in its header, the `[[wikilinks]]` to the very docs this MCP serves, and `docs/CODEMAP.md` is the generated inverse index. The block's rules are owned by [[adr-17-live-doc-backlinks]], its file→link mapping by the linker manifest, and its stamping by the `kdx-live-doc` skill ([[HARNESS]]) — **never hand-authored**. Reproduced here as reference only:

| File type | Wrapper for the `LIVE-DOC:START … LIVE-DOC:END` block |
|---|---|
| `*.py` | module **docstring** `"""…"""` at line 1 |
| `*.astro` | `/* … */` immediately after the front-matter `---` fence |
| `*.svelte` | `<!-- … -->` |
| `*.ts` / `*.js` | `/* … */` |
| backend `*.html` | `{# … #}` |
| `*.yaml` / `compose` | `# …` |

A `.py` file's block is its module docstring; a `.astro` file's block is a comment after its fence. The `<slug>` in the header is parametrized — the linker reads it from the `PROJECT_SLUG` env var ([[VARIABLES]]), falling back to this template's reference slug. Example, as `kdx-live-doc` stamps it into `backend/config/settings.py`:

```python
"""LIVE-DOC:START — <slug> live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-02-initial-stack]] · [[adr-06-cache]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[VARIABLES]]
LIVE-DOC:END"""
```

The block holds **links only, never prose** ([[adr-17-live-doc-backlinks]] rule 2). To change which docs a file cites, edit the manifest and re-run the linker — not the block by hand. `models.py` / `views.py` / `viewsets.py` / `serializers.py` / `urls.py` / permission classes additionally cite `[[API]]` (rule 4).

## Relationship to the other tools

- **`codebase-memory-mcp`** answers code-structure questions (functions, call chains, routes). The markdown-vault MCP answers `docs/` questions. They are disjoint and neither replaces the other ([[adr-18-markdown-vault-mcp]] rule 4).
- **`obsidian-markdown`** skill is how vault prose is *written* correctly (frontmatter, callouts, embeds). This MCP is how it is *found, read, and traversed*.
