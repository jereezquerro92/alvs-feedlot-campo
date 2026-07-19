"""Anti-hardcode guard for the project slug (issue #133).

The literal string this template ships as its reference project slug MUST
NOT appear typed out across the tree — the single source of truth is the
`PROJECT_SLUG` environment variable (frontend-derived form:
`PUBLIC_PROJECT_SLUG`), never a copy-pasted literal. See docs/VARIABLES.md
("Sanctioned PROJECT_SLUG consumption points") for the full inventory this
allowlist encodes, and docs/GLOSSARY.md ("project slug" row) for the naming
decision.

These are the well-determined places the literal may still appear:
  (a) the file is a Markdown doc (`*.md`) — narrative/reference prose is
      exempt whole-file;
  (b) the file is `.env` or `.env.example` — local dev config, not app code;
  (c) the line also contains the literal `PROJECT_SLUG` — every sanctioned
      single-source fallback carries this token alongside the literal, e.g.
      `os.environ.get("PROJECT_SLUG", "<slug>")`,
      `${PROJECT_SLUG:-<slug>}`, `PUBLIC_PROJECT_SLUG ?? "<slug>"`, or the
      deploy workflow's `PROJECT_SLUG: <slug>` line — the literal there is
      the one legitimate seed value, not a stray copy;
  (d) the line also contains `LIVE-DOC` — a generated live-doc block header
      (adr-17-live-doc-backlinks), not a hardcode;
  (e) a short, explicit EXCEPTIONS list below, for opaque values that are
      not derivable from PROJECT_SLUG at all: `.github/workflows/
      deploy-prod.yml` lines holding one of the six AWS-random-suffix ARNs
      baked in at provisioning time (issue #129); `.claude/hooks/
      graph_first.py`'s codebase-memory-mcp project id (a different
      identifier namespace, not this app's PROJECT_SLUG);
      `tests/test_graph_first_hook.py`'s derivation fixtures — it types a
      sample checkout path and the retired literal to prove graph_first.py
      derives the id at runtime and to guard against the literal's return,
      the same self-referential need rule (f) grants this guard; and
      `.claude/kdx-park.json`'s `repo` routing target — kdx-draft-issue's
      park-mode file, harness tooling, not this app's PROJECT_SLUG (#307);
  (f) this test file itself — it necessarily types the literal it searches
      for;
  (g) a guardian name — `astro-drf-aws-prd`, `astro-drf-aws-adr`, or
      `astro-drf-aws-api` — is a SEPARATE naming axis (an agent identity,
      not the project slug), guarded on its own by
      `tests/test_guardian_identity_triangle.py`. A line is allowed under
      this rule if, after stripping every guardian-name token, no bare
      `astro-drf-aws` remains on it; a bare occurrence (not part of a
      guardian token) still fails.

Anything else is a hardcode and fails the test.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

SLUG = "astro-drf-aws"

# rule (g): guardian names are a separate naming axis (agent identities),
# guarded on their own by tests/test_guardian_identity_triangle.py — not a
# PROJECT_SLUG hardcode. `\b` keeps a suffix like `-prdx` from matching.
GUARDIAN_NAME_RE = re.compile(r"astro-drf-aws-(?:prd|adr|api)\b", re.IGNORECASE)

EXCLUDE_DIR_NAMES = {".git", "node_modules", ".astro", "dist", ".venv", ".mvmcp"}

# (file relative to ROOT, POSIX path; substring that must appear in the
# offending line; reason) — rule (e). Matched by content substring, never
# by line number, so the exception survives surrounding edits.
EXCEPTIONS: list[tuple[str, str, str]] = [
    (
        ".github/workflows/deploy-prod.yml",
        "SECRET_DJANGO",
        "opaque Secrets Manager ARN, random suffix baked at provisioning time",
    ),
    (
        ".github/workflows/deploy-prod.yml",
        "SECRET_DB",
        "opaque Secrets Manager ARN, random suffix baked at provisioning time",
    ),
    (
        ".github/workflows/deploy-prod.yml",
        "SECRET_COGNITO",
        "opaque Secrets Manager ARN, random suffix baked at provisioning time",
    ),
    (
        ".github/workflows/deploy-prod.yml",
        "SECRET_MSGRAPH",
        "opaque Secrets Manager ARN, random suffix baked at provisioning time",
    ),
    (
        ".claude/hooks/graph_first.py",
        "home-kodex-Templates-astro-drf-aws",
        "codebase-memory-mcp project id — a filesystem-path-derived "
        "identifier, not this app's PROJECT_SLUG",
    ),
    (
        "tests/test_graph_first_hook.py",
        "astro-drf-aws",
        "derivation regression fixtures — a sample checkout path and the "
        "retired literal, typed to prove graph_first.py derives the "
        "codebase-memory project id at runtime; the same self-referential "
        "need rule (f) grants this guard",
    ),
    (
        ".claude/kdx-park.json",
        '"repo"',
        "kdx-draft-issue park-mode routing target (owner/repo for GitHub); "
        "harness-tooling state, not app PROJECT_SLUG — same carve-out "
        "rationale as scripts/ per #307",
    ),
]
# Note: dispatch_guardians.py's three WATCHLISTS guardian-name keys used to
# need an explicit entry here; they are now covered by the general rule (g)
# below (GUARDIAN_NAME_RE), so no per-file exception is needed for them.


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise AssertionError(msg)


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def tracked_files() -> list[Path]:
    """Prefer `git ls-files` (respects .gitignore, no extra filtering
    needed); fall back to an excludes-aware rglob if git is unavailable."""
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return [ROOT / line for line in proc.stdout.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        out: list[Path] = []
        for p in ROOT.rglob("*"):
            if not p.is_file():
                continue
            if any(part in EXCLUDE_DIR_NAMES for part in p.relative_to(ROOT).parts):
                continue
            out.append(p)
        return out


def is_excepted(rel: str, line: str) -> bool:
    for exc_file, needle, _reason in EXCEPTIONS:
        if rel == exc_file and needle in line:
            return True
    return False


def scan_file(path: Path) -> list[str]:
    if path.resolve() == SELF:
        return []  # rule (f)

    rel = path.relative_to(ROOT).as_posix()
    if rel.endswith(".md"):
        return []  # rule (a)
    if path.name in (".env", ".env.example"):
        return []  # rule (b)

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []  # binary / unreadable — not a text hardcode

    offenders: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if SLUG.lower() not in line.lower():
            continue
        if "PROJECT_SLUG" in line:  # rule (c)
            continue
        if "LIVE-DOC" in line:  # rule (d)
            continue
        if is_excepted(rel, line):  # rule (e)
            continue
        stripped = GUARDIAN_NAME_RE.sub("", line)
        if SLUG.lower() not in stripped.lower():  # rule (g)
            continue
        offenders.append(f"{rel}:{lineno}:{line.strip()}")
    return offenders


def test_no_hardcoded_project_slug() -> None:
    offenders: list[str] = []
    for f in tracked_files():
        offenders.extend(scan_file(f))

    if offenders:
        detail = "\n  ".join(offenders)
        fail(
            f"{len(offenders)} hardcoded occurrence(s) of {SLUG!r} outside "
            f"the sanctioned allowlist (docs/VARIABLES.md — 'Sanctioned "
            f"PROJECT_SLUG consumption points'):\n  {detail}"
        )
    ok(f"zero hardcoded occurrences of {SLUG!r} outside the sanctioned allowlist")


def main() -> int:
    tests = [test_no_hardcoded_project_slug]
    failed = 0
    for fn in tests:
        try:
            fn()
        except AssertionError:
            failed += 1
        except Exception as exc:
            print(f"FAIL: {fn.__name__}: {exc}", file=sys.stderr)
            failed += 1

    if failed:
        print(f"\n{failed} test(s) failed", file=sys.stderr)
        return 1
    print(f"\nall {len(tests)} test(s) passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
