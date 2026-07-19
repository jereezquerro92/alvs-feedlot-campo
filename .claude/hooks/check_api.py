#!/usr/bin/env python3
"""API contract hook (PostToolUse on Write|Edit).

Enforces adr-03-api-and-backend rule 1 on every urls.py written: each route
literal (path/re_path/router.register) must correspond to an endpoint row in
docs/API.md. urls.py declares relative segments, so a route matches only when
its full ordered sequence of literal segments appears — in order — within a
single declared docs/API.md path (params like <id> are skippable filler).
Exit 2 feeds the violation back to the agent; any internal error exits 0.
"""

import json
import os
import re
import sys
from pathlib import Path

ROW = re.compile(
    r"^\|\s*(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|WS)\s*\|\s*`(/[^`]*)`",
    re.MULTILINE,
)
ROUTE = re.compile(r"""(?:re_)?path\(\s*r?["']([^"']*)["']""")
REGISTER = re.compile(r"""\.register\(\s*r?["']([^"']*)["']""")


def project_dir():
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


def declared_paths():
    api = project_dir() / "docs" / "API.md"
    try:
        return ROW.findall(api.read_text(encoding="utf-8"))
    except OSError:
        return None


def literal_segments(route):
    route = route.strip().lstrip("^").rstrip("$")
    segments = []
    for part in route.split("/"):
        if not part or part.startswith("<") or not re.fullmatch(r"[a-zA-Z0-9_-]+", part):
            continue
        segments.append(part)
    return segments


def _declared_segment_lists(declared):
    return [[s for s in p.strip("/").split("/") if s] for p in declared]


def _is_ordered_subsequence(needle, haystack):
    it = iter(haystack)
    return all(seg in it for seg in needle)


def check(path):
    if path.name != "urls.py" or "/.claude/" in path.as_posix():
        return []
    try:
        code = path.read_text(encoding="utf-8")
    except OSError:
        return []
    declared = declared_paths()
    if declared is None:
        return []
    declared_segments = _declared_segment_lists(declared)
    problems = []
    for route in ROUTE.findall(code) + REGISTER.findall(code):
        segments = literal_segments(route)
        if not segments:
            continue
        if not any(_is_ordered_subsequence(segments, dsl) for dsl in declared_segments):
            problems.append(
                f"{path.name}: route '{route}' is not declared in docs/API.md — "
                "its full segment sequence appears in no endpoint row; an endpoint "
                "is valid if and only if it is declared there "
                "(adr-03-api-and-backend). Add the row first, then the route."
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
