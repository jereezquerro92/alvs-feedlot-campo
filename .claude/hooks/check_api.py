#!/usr/bin/env python3
"""API contract + membrane hook (PostToolUse on Write|Edit).

Backend half (adr-51-api-and-backend rule 1): every *urls.py route literal
(urls.py, api_urls.py, … — path/re_path/router.register) must correspond to
an endpoint row in docs/API.md. Route modules declare relative segments, so a
route matches only when its full ordered sequence of literal segments appears
— in order — within a single declared docs/API.md path (params like <id> are
skippable filler).

Frontend half (adr-53-api-membrane rule 2): a frontend file under frontend/src
- MUST NOT fetch a path whose literal segment sequence matches no declared
  docs/API.md row (the frontend's endpoint-existence obligation, mirroring
  the backend's);
- MUST NOT name a backend internal — the framework, the ORM, a serializer,
  a viewset, an app-internal module path, or a migration — in code, comment
  or docstring. `PUBLIC_BACKEND_URL`/`backendApiUrl`/`publicBackendUrl` are
  the membrane's address, never a leak (adr-53 rule 3), and are exempt.

Exit 2 feeds the violation back to the agent; any internal error exits 0.
This is a local, bypassable hook, not a barrier (adr-53 rule 6).
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

FRONTEND_EXTS = (".ts", ".svelte", ".astro")

# Backend-internal knowledge forbidden in frontend files (adr-53 rule 2).
# Deliberately narrow and mechanical: markers that only ever show up when a
# file actually names a framework/ORM/backend-internal detail, never in
# ordinary English prose ("model", "Django" used descriptively in a comment
# about auth architecture, the project slug, etc.).
BACKEND_MARKERS = [
    (re.compile(r"\brest_framework\b"), "imports/names the rest_framework package"),
    (re.compile(r"(?<![-\w])DRF(?![-\w])"), "names DRF (Django REST Framework)"),
    (re.compile(r"\bdjango\.db\b|\bdjango\.contrib\b|\bdjango\.forms\b"),
     "names a django.* internal module path"),
    (re.compile(r"\bapps\.[a-z][a-z0-9_]*\.(models|serializers|viewsets|views|admin)\b"),
     "names a backend app's internal module (apps.<app>.<module>)"),
    (re.compile(r"\b(?:models|serializers|viewsets|views|admin)\.py\b"),
     "names a backend source file"),
    (re.compile(r"\b[A-Z]\w*Serializer\b"), "names a DRF serializer class"),
    (re.compile(r"\b[A-Z]\w*ViewSet\b"), "names a DRF viewset class"),
    (re.compile(r"\.objects\.(filter|get|create|all|exclude)\("),
     "uses Django ORM manager syntax (.objects.<method>()"),
    (re.compile(r"\bQuerySet\b"), "names the Django ORM QuerySet type"),
    (re.compile(r"\bmigrations/0\d{3}_"), "names a Django migration file"),
]


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


def _is_backend_route_module(path):
    # Match urls.py and aliases included from config (e.g. api_urls.py).
    return path.name.endswith("urls.py") and "/.claude/" not in path.as_posix()


def check_backend_urls(path):
    if not _is_backend_route_module(path):
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
                "(adr-51-api-and-backend). Add the row first, then the route."
            )
    return problems


FETCH_TEMPLATE = re.compile(r"fetch\(\s*`([^`]*)`")
TEMPLATE_EXPR = re.compile(r"\$\{[^}]*\}")


def _fetch_path_segments(template_str):
    """Extract literal, checkable segments from a fetch(`...`) template
    string. A segment that is wholly a ${...} interpolation is dynamic and
    skippable (mirrors <id> in urls.py); a segment mixing literal text with
    an interpolation (e.g. a base-URL variable glued to a following path,
    `${backendApiUrl}${path}`) cannot be resolved statically and yields no
    segments at all — the file is then left unchecked rather than guessed at
    (precision over coverage)."""
    segments = []
    for part in template_str.split("/"):
        part = part.strip()
        if not part:
            continue
        if TEMPLATE_EXPR.fullmatch(part):
            continue
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", part):
            return []
        segments.append(part)
    return segments


def check_frontend_routes(path, text, declared_segments):
    problems = []
    for template_str in FETCH_TEMPLATE.findall(text):
        segments = _fetch_path_segments(template_str)
        if not segments:
            continue
        if not any(_is_ordered_subsequence(segments, dsl) for dsl in declared_segments):
            problems.append(
                f"{path.name}: fetch to '{template_str}' has no matching row in "
                "docs/API.md — its full segment sequence appears in no declared "
                "endpoint; the frontend may call only what docs/API.md declares "
                "(adr-53-api-membrane rule 2, adr-51-api-and-backend rule 1)."
            )
    return problems


# PUBLIC_BACKEND_URL and its local aliases are the membrane's address, not a
# leak (adr-53 rule 3) — never flagged by BACKEND_MARKERS below.
_MEMBRANE_ADDRESS = re.compile(
    r"\bPUBLIC_BACKEND_URL\b|\bpublicBackendUrl\b|\bbackendApiUrl\b|\bBACKEND_API_URL\b"
)


def check_frontend_knowledge(path, text):
    problems = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        scrubbed = _MEMBRANE_ADDRESS.sub("", line)
        for marker, why in BACKEND_MARKERS:
            if marker.search(scrubbed):
                problems.append(
                    f"{path.name}:{lineno}: frontend file {why} — forbidden backend "
                    "knowledge in frontend code, comment or docstring "
                    "(adr-53-api-membrane rule 2, rule 5). Only what a docs/API.md "
                    "row states may be known here."
                )
                break
    return problems


def check_frontend(path):
    posix = path.resolve().as_posix()
    if "/frontend/src/" not in posix or path.suffix not in FRONTEND_EXTS:
        return []
    if "/node_modules/" in posix:
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    problems = check_frontend_knowledge(path, text)
    declared = declared_paths()
    if declared is not None:
        problems += check_frontend_routes(path, text, _declared_segment_lists(declared))
    return problems


def check(path):
    if _is_backend_route_module(path):
        return check_backend_urls(path)
    return check_frontend(path)


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
