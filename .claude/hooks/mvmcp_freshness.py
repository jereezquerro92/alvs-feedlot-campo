#!/usr/bin/env python3
"""markdown-vault MCP freshness guard (SessionStart).

The markdown-vault-docs MCP is the first source of truth for docs/ content
([[adr-18-markdown-vault-mcp]], [[AGENTS]]). A stale index answers confidently
about prose that no longer matches, so this hook compares the newest docs/*.md
mtime against the project-local index and warns when the vault has drifted — and
tells the agent to bootstrap when the project-local venv/index does not exist yet.
It never blocks; any internal error exits 0 (fail-open).

Bootstrap / rebuild:  python3 scripts/mvmcp.py bootstrap
Incremental refresh:  call the markdown-vault-docs `reindex` tool.
"""

import os
import sys
from pathlib import Path

SKIP_DIRS = {".git", ".obsidian", ".vscode"}


def project_dir():
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env) if env else Path(__file__).resolve().parents[2]


def newest_docs_mtime(docs):
    newest = 0.0
    for dirpath, dirnames, filenames in os.walk(docs):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".md"):
                try:
                    newest = max(newest, (Path(dirpath) / name).stat().st_mtime)
                except OSError:
                    pass
    return newest


def main():
    try:
        root = project_dir()
        binary = root / ".mvmcp" / ".venv" / "bin" / "markdown-vault-mcp"
        index = root / ".mvmcp" / "data" / "index.db"
        if not binary.exists() or not index.exists():
            print(
                "MARKDOWN-VAULT MCP — BOOTSTRAP FIRST: the project-local vault index "
                "does not exist yet. The markdown-vault-docs MCP is the first source "
                "of truth for docs/ content and cannot answer until it is built. Run: "
                "python3 scripts/mvmcp.py bootstrap"
            )
            return 0
        newest = newest_docs_mtime(root / "docs")
        if newest > index.stat().st_mtime:
            print(
                "MARKDOWN-VAULT MCP — REINDEX FIRST: docs/ has changed since the "
                "markdown-vault-docs index was last built. It is STALE; refresh before "
                "trusting its search/read/backlinks. Call the markdown-vault-docs "
                "`reindex` tool, or run: python3 scripts/mvmcp.py bootstrap"
            )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
