#!/usr/bin/env python3
"""Graph-first discipline gate (PreToolUse: Grep|Glob).

The codebase-memory graph is the FIRST source of truth for code questions here
(SessionStart Code Discovery Protocol). This hook does not block text search —
Grep/Glob stay free for docs, configs and non-code files, and Read is untouched.
It only *challenges* (permissionDecision "ask") a search that looks like a code-
symbol hunt over Python source, where search_graph / trace_path / search_code
would resolve it precisely. Any internal error exits 0 (fail-open).

The challenge requires an explicit Python target: a repo-wide sweep with no path
is a text search until it says otherwise. And it never fires in a cloud session
(CLAUDE_CODE_REMOTE) — the graph is machine-global and deliberately not vendored
([[HARNESS]], [[adr-18-markdown-vault-mcp]] rule 4), so there is nothing there to
prefer over Grep, and an "ask" no human can answer would stall the session.

Escalate the one matcher below from "ask" to "deny" if discipline still slips.
"""

import json
import os
import re
import sys

# High-signal "this is a code symbol" patterns.
SYMBOL_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CODE_TOKEN = re.compile(r"\b(def|class|async\s+def|import|from|self\.)\b")

# Text-search intent that is clearly NOT a graph question — let it pass.
NONCODE_HINT = re.compile(
    r"\.(md|ya?ml|json|toml|txt|lock|cfg|ini|env)\b|Dockerfile|compose|\.env",
    re.IGNORECASE,
)
# Paths whose content is not indexed code.
NONCODE_PATH = re.compile(r"(^|/)(docs|\.claude|\.agents|agents|tests)(/|$)")


def looks_like_code_search(tool_input):
    path = str(tool_input.get("path", "") or "")
    glob = str(tool_input.get("glob", "") or "")
    pattern = str(tool_input.get("pattern", "") or "")

    # Explicitly non-code target -> not our business.
    if NONCODE_HINT.search(glob) or NONCODE_HINT.search(pattern):
        return False
    if path and NONCODE_PATH.search(path):
        return False

    # In scope only when the search names Python source explicitly.
    touches_py = "backend" in path or ".py" in glob or ".py" in pattern
    if not touches_py:
        return False

    # And only when the pattern reads like a symbol, not prose.
    return bool(SYMBOL_PATTERN.match(pattern.strip()) or CODE_TOKEN.search(pattern))


def graph_is_reachable():
    return os.environ.get("CLAUDE_CODE_REMOTE", "").lower() != "true"


def codebase_memory_project_id():
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return os.path.abspath(root).lstrip("/").replace("/", "-")


def main():
    try:
        if not graph_is_reachable():
            return 0
        payload = json.load(sys.stdin)
        tool_input = payload.get("tool_input", {}) or {}
        if not looks_like_code_search(tool_input):
            return 0
        project = codebase_memory_project_id()
        reason = (
            "Graph-first: this looks like a code-symbol search over Python source. "
            "The codebase-memory graph is the first source of truth here — prefer "
            "search_graph (definitions/routes), trace_path (call chains) or "
            "search_code (graph-augmented grep) with "
            f"project='{project}'. Proceed with "
            "Grep/Glob only if this is genuinely a text search the graph can't answer."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": reason,
            }
        }))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
