#!/usr/bin/env python3
"""ADR conformance hook (PostToolUse on Write|Edit).

Enforces adr-00-adr-doctrine on every file written under .claude/rules/ or
docs/adrs/: filename pattern, required frontmatter, the intentional `defered`
spelling (GLOSSARY forbids `deferred`), and an empty body when defered.
Exit 2 feeds the violation back to the agent; any internal error exits 0.
"""

import json
import os
import re
import sys
from pathlib import Path

FILENAME = re.compile(r"^adr-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
REQUIRED_KEYS = ("title", "type", "status", "created")


def project_dir():
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


def parse(text):
    match = re.match(r"\A---\n(.*?)\n---\n?(.*)\Z", text, re.DOTALL)
    if not match:
        return None, text
    fm = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm, match.group(2)


def check(path):
    posix = path.as_posix()
    if "/.claude/rules/" not in posix and "/docs/adrs/" not in posix:
        return []
    if path.suffix != ".md":
        return []
    problems = []
    if not FILENAME.match(path.name):
        problems.append(
            f"{path.name}: ADR filenames must match adr-NN-slug.md "
            "(sequential NN, kebab-case English slug) per adr-00-adr-doctrine."
        )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return problems
    if re.search(r"\bdeferred\b", text, re.IGNORECASE):
        problems.append(
            f"{path.name}: forbidden form 'deferred' — the lifecycle token is "
            "spelled 'defered' (GLOSSARY; intentional, machine-checked)."
        )
    fm, body = parse(text)
    if fm is None:
        problems.append(f"{path.name}: missing frontmatter block (adr-00-adr-doctrine).")
        return problems
    for key in REQUIRED_KEYS:
        if key not in fm:
            problems.append(f"{path.name}: frontmatter lacks '{key}' (adr-00-adr-doctrine).")
    if fm.get("type") and fm["type"] != "adr":
        problems.append(f"{path.name}: frontmatter 'type' must be 'adr', found '{fm['type']}'.")
    status = fm.get("status")
    if status and status not in ("active", "defered"):
        problems.append(
            f"{path.name}: status must be 'active' or 'defered', found '{status}'."
        )
    if status == "defered" and body.strip():
        problems.append(
            f"{path.name}: a defered ADR keeps ONLY its frontmatter; move the body "
            "to docs/obsolete/defered-adr-NN-slug.md (adr-00-adr-doctrine)."
        )
    return problems


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
