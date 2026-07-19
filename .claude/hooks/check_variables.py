#!/usr/bin/env python3
"""Environment-variable SSOT hook (PostToolUse on Write|Edit).

Enforces the VARIABLES doctrine (adr-03 rule 7): a variable used in code but
not declared in docs/VARIABLES.md does not exist. VARIABLES governs what the
backend and frontend services read, so the sweep is scoped to those two trees
plus the committed .env* templates. Harness tooling — repo-root tests/, scripts/,
.claude/hooks/ — reads env as CLI knobs, never as app runtime, and is out of
scope by the same rule ([[adr-18-markdown-vault-mcp]] rule 3 states this outright
for the vault launcher).
Exit 2 feeds the violation back to the agent; any internal error exits 0.
"""

import json
import os
import re
import sys
from pathlib import Path

DECLARED_ROW = re.compile(r"^\|\s*`([A-Z][A-Z0-9_]*)`\s*\|", re.MULTILINE)
ENV_ASSIGNMENT = re.compile(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=", re.MULTILINE)
CODE_READS = (
    re.compile(r"""os\.environ(?:\.get)?\(\s*["']([A-Z][A-Z0-9_]*)["']"""),
    re.compile(r"""os\.environ\[\s*["']([A-Z][A-Z0-9_]*)["']\s*\]"""),
    re.compile(r"""os\.getenv\(\s*["']([A-Z][A-Z0-9_]*)["']"""),
    re.compile(r"""process\.env\.([A-Z][A-Z0-9_]*)"""),
    re.compile(r"""import\.meta\.env\.([A-Z][A-Z0-9_]*)"""),
    re.compile(r"""Bun\.env\.([A-Z][A-Z0-9_]*)"""),
    # settings.py reads env only through its _env/_env_bool/_env_list helpers
    # (backend/config/settings.py) — without this pattern the hook is blind to
    # the file that consumes every declared variable.
    re.compile(r"""\b_env(?:_bool|_list)?\(\s*["']([A-Z][A-Z0-9_]*)["']"""),
)
CODE_SUFFIXES = {".py", ".js", ".mjs", ".cjs", ".ts", ".mts", ".astro", ".svelte"}
RUNTIME_BUILTINS = {"PROD", "DEV", "MODE", "SSR", "BASE_URL", "SITE"}
SERVICE_TREES = ("backend", "frontend")


def project_dir():
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


def declared_names():
    variables = project_dir() / "docs" / "VARIABLES.md"
    try:
        return set(DECLARED_ROW.findall(variables.read_text(encoding="utf-8")))
    except OSError:
        return None


def used_names(path, text):
    if path.name.startswith(".env"):
        return set(ENV_ASSIGNMENT.findall(text))
    if path.suffix in CODE_SUFFIXES:
        found = set()
        for pattern in CODE_READS:
            found.update(pattern.findall(text))
        return found
    return set()


def in_scope(path):
    root = project_dir().resolve()
    if path.name.startswith(".env"):
        return path.parent == root
    return any(path.is_relative_to(root / tree) for tree in SERVICE_TREES)


def check(path):
    if not in_scope(path):
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    declared = declared_names()
    if declared is None:
        return []
    undeclared = sorted(used_names(path, text) - declared - RUNTIME_BUILTINS)
    if not undeclared:
        return []
    return [
        f"{path.name}: variable(s) {', '.join(undeclared)} not declared in "
        "docs/VARIABLES.md — a variable used in code but not declared there "
        "does not exist (VARIABLES change protocol). Add the row first."
    ]


def main():
    try:
        payload = json.load(sys.stdin)
        file_path = payload.get("tool_input", {}).get("file_path", "")
        if not file_path:
            return 0
        target = Path(file_path).resolve()
        if not target.is_relative_to(project_dir().resolve()):
            return 0
        problems = check(target)
    except Exception:
        return 0
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
