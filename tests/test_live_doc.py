"""Harness test for the live-doc linker ([[adr-17-live-doc-backlinks]], [[HARNESS]]).

Asserts the block invariants without re-implementing the linker: no drift, exactly
one block per matched file, wikilinks-only bodies, API cited by the route surface,
and CODEMAP.md in sync. Run: python3 tests/test_live_doc.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude" / "skills" / "kdx-live-doc"
LINKER = SKILL / "link.py"
MANIFEST = json.loads((SKILL / "manifest.json").read_text())
START, END = "LIVE-DOC:START", "LIVE-DOC:END"
API_TRIGGERS = ("models.py", "views.py", "viewsets.py", "serializers.py",
                "urls.py", "api_urls.py", "permissions.py")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise AssertionError(msg)


def ok(msg: str) -> None:
    print(f"ok  {msg}")


def block_body(text: str) -> list[str] | None:
    """Return the lines strictly between the START and END markers, or None."""
    lines = text.splitlines()
    s = e = None
    for i, ln in enumerate(lines):
        if START in ln and s is None:
            s = i
        elif END in ln and s is not None:
            e = i
            break
    if s is None or e is None:
        return None
    return lines[s + 1:e]


def matched_files() -> list[Path]:
    from fnmatch import fnmatch
    excl = set(MANIFEST["exclude_dirs"])
    out = []
    for root in MANIFEST["roots"]:
        p = ROOT / root
        cands = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
        for f in cands:
            if any(part in excl for part in f.parts):
                continue
            if not f.stat().st_size or f.name.endswith(".d.ts"):
                continue
            rel = f.relative_to(ROOT).as_posix()
            if any(fnmatch(rel, r["glob"]) or fnmatch(rel, "**/" + r["glob"])
                   for r in MANIFEST["rules"]):
                out.append(f)
    return out


def main() -> None:
    assert LINKER.exists(), "linker missing"
    ok("linker present")

    # 1. No drift — the committed tree matches what the linker would produce.
    r = subprocess.run([sys.executable, str(LINKER), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        fail(f"live-doc drift — run link.py to re-sync:\n{r.stdout}\n{r.stderr}")
    ok("no drift (link.py --check clean)")

    files = matched_files()
    assert files, "manifest matched zero files"
    ok(f"{len(files)} matched files")

    wikilink = re.compile(r"\[\[[^\]]+\]\]")
    prose_line = re.compile(r"^(Governed by:|Docs:|API:)")
    for f in files:
        text = f.read_text()
        # 2. exactly one block
        if text.count(START) != 1 or text.count(END) != 1:
            fail(f"{f}: expected exactly one live-doc block")
        body = block_body(text)
        # 3. wikilinks only — every body line is a known label line and holds a wikilink
        for ln in body:
            stripped = re.sub(r"^[\s#*/{}<>!-]+", "", ln).rstrip("#-} */>").strip()
            if not stripped:
                continue
            if not prose_line.match(stripped):
                fail(f"{f}: block carries non-link prose: {ln!r}")
            if not wikilink.search(stripped):
                fail(f"{f}: block line without a wikilink: {ln!r}")
        # 4. route surface cites API
        if f.name in API_TRIGGERS and f.as_posix().find("/backend/") != -1:
            if "[[API]]" not in text:
                fail(f"{f}: route-surface file must cite [[API]]")
    ok("every block is wikilinks-only; route surface cites [[API]]")

    # 5. CODEMAP exists and points at the ruling ADR
    codemap = (ROOT / "docs" / "CODEMAP.md").read_text()
    assert "adr-17-live-doc-backlinks" in codemap, "CODEMAP missing ADR link"
    ok("CODEMAP.md present and linked")

    print("\nALL LIVE-DOC CHECKS PASSED")


if __name__ == "__main__":
    main()
