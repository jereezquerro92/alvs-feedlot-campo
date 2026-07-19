#!/usr/bin/env python3
"""SSOT preload hook (SessionStart).

Gives force to the AGENTS.md standing requirement: PRD and API MUST be held
in memory at all times. Injects the current contents of docs/PRD.md and
docs/API.md into context at session start (startup, resume, and clear alike),
so the requirement is met deterministically instead of by obedience.
Stdout is added to context; any internal error exits 0.
"""

import os
import sys
from pathlib import Path

SSOT_FILES = ("docs/PRD.md", "docs/API.md")


def project_dir():
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


def main():
    try:
        root = project_dir()
        sections = []
        for relative in SSOT_FILES:
            path = root / relative
            try:
                sections.append(f"=== {relative} ===\n{path.read_text(encoding='utf-8').strip()}")
            except OSError:
                sections.append(f"=== {relative} === (unreadable — read it manually before acting)")
        print(
            "SSOT preload (AGENTS.md standing requirement — PRD and API are held "
            "in memory at all times; re-read them whenever they change):\n\n"
            + "\n\n".join(sections)
        )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
