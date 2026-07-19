#!/usr/bin/env python3
"""Graph freshness guard (SessionStart).

Using a stale graph first is worse than not using it: it answers confidently
about code that no longer matches. This hook compares the mtime of indexed
source against a marker stamped at the last reindex, and — when source has
drifted — injects a loud REINDEX-FIRST warning into context. It never blocks;
it only warns. Any internal error exits 0 (fail-open).

The marker is `.claude/.graph-index-marker` (git-ignored). Stamp it after every
reindex:  touch "$CLAUDE_PROJECT_DIR/.claude/.graph-index-marker"
"""

import os
import sys
from pathlib import Path

MARKER = ".claude/.graph-index-marker"
SOURCE_ROOTS = ("backend", "tests")
ROOT_FILES = ("compose.yaml",)
SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules"}


def project_dir():
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env) if env else Path(__file__).resolve().parents[2]


def newest_source_mtime(root):
    newest = 0.0
    for base in SOURCE_ROOTS:
        for dirpath, dirnames, filenames in os.walk(root / base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if name.endswith((".py", ".yaml", ".yml")):
                    try:
                        newest = max(newest, (Path(dirpath) / name).stat().st_mtime)
                    except OSError:
                        pass
    for name in ROOT_FILES:
        try:
            newest = max(newest, (root / name).stat().st_mtime)
        except OSError:
            pass
    return newest


def main():
    try:
        root = project_dir()
        marker = root / MARKER
        newest = newest_source_mtime(root)
        stamp = marker.stat().st_mtime if marker.exists() else 0.0
        if newest > stamp:
            print(
                "GRAPH FRESHNESS — REINDEX FIRST: source has changed since the "
                "codebase-memory graph was last indexed. The graph is STALE; do "
                "NOT trust search_graph/trace_path until you refresh it. Run "
                "index_repository(repo_path='" + str(root) + "', mode='full'), "
                "then stamp: touch " + str(marker)
            )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
