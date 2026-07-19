#!/usr/bin/env python3
"""Live-doc linker for this template.

Reads manifest.json, stamps an idempotent LIVE-DOC block (wikilinks only, no
prose) onto every matched code file, and regenerates docs/CODEMAP.md — the
generated doc->code index. Governed by [[adr-17-live-doc-backlinks]].

Usage:
    python3 .claude/skills/kdx-live-doc/link.py            # apply + write CODEMAP
    python3 .claude/skills/kdx-live-doc/link.py --check    # report only, non-zero if drift
"""
from __future__ import annotations

import json
import os
import sys
from fnmatch import fnmatch
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILL = Path(__file__).resolve().parent
MANIFEST = json.loads((SKILL / "manifest.json").read_text())
START = "LIVE-DOC:START"
END = "LIVE-DOC:END"
ADR_REF = "[[adr-17-live-doc-backlinks]]"
# Naming authority: [[GLOSSARY]] ([[adr-01-glossary-and-localization]]); runtime carrier: PROJECT_SLUG ([[VARIABLES]]).
SLUG = os.environ.get("PROJECT_SLUG", "astro-drf-aws")


def link_set(rel: str) -> list[str]:
    """Ordered union of every matching rule's links."""
    out: list[str] = []
    for rule in MANIFEST["rules"]:
        if fnmatch(rel, rule["glob"]) or fnmatch(rel, "**/" + rule["glob"]):
            for lk in rule["links"]:
                if lk not in out:
                    out.append(lk)
    return out


def grouped_lines(links: list[str]) -> list[str]:
    adrs = [l for l in links if l.startswith("adr-")]
    api = [l for l in links if l == "API"]
    docs = [l for l in links if l not in adrs and l not in api]
    lines = []
    if adrs:
        lines.append("Governed by: " + " · ".join(f"[[{a}]]" for a in adrs))
    if docs:
        lines.append("Docs: " + " · ".join(f"[[{d}]]" for d in docs))
    if api:
        lines.append("API: [[API]]")
    return lines


# ---- wrappers: return the full block as a list of lines ----------------------

def block_hash_comment(prefix: str, body: list[str]) -> list[str]:
    out = [f"{prefix} {START} — {SLUG} live-doc; see {ADR_REF}"]
    out += [f"{prefix} {b}" for b in body]
    out.append(f"{prefix} {END}")
    return out


def block_c_comment(body: list[str]) -> list[str]:
    out = [f"/* {START} — {SLUG} live-doc; see {ADR_REF}"]
    out += [f" * {b}" for b in body]
    out.append(f" * {END} */")
    return out


def block_html_comment(body: list[str]) -> list[str]:
    out = [f"<!-- {START} — {SLUG} live-doc; see {ADR_REF}"]
    out += [f"     {b}" for b in body]
    out.append(f"     {END} -->")
    return out


def block_django_comment(body: list[str]) -> list[str]:
    out = [f"{{# {START} — {SLUG} live-doc; see {ADR_REF}"]
    out += [f"   {b}" for b in body]
    out.append(f"   {END} #}}")
    return out


def strip_block(lines: list[str]) -> list[str]:
    """Remove the marked region (inclusive) if present. Also drops a bare docstring
    that contained only our region (leaves no orphan quotes)."""
    s = e = None
    for i, ln in enumerate(lines):
        if START in ln and s is None:
            s = i
        if END in ln and s is not None:
            e = i
            break
    if s is None or e is None:
        return lines
    # If the START line opens a python docstring and END line closes it, drop both.
    return lines[:s] + lines[e + 1:]


def insert_py(text: str, body: list[str]) -> str:
    lines = text.splitlines()
    lines = strip_block(lines)
    # keep shebang / coding line on top
    head = 0
    while head < len(lines) and (lines[head].startswith("#!") or "coding" in lines[head][:40] and lines[head].startswith("#")):
        head += 1
    # skip blanks
    j = head
    while j < len(lines) and lines[j].strip() == "":
        j += 1
    doc = [f'"""{START} — {SLUG} live-doc; see {ADR_REF}']
    doc += body
    doc.append(f'{END}"""')
    new = lines[:head]
    if head < len(lines) and lines[head].startswith("#!"):
        new.append("")  # blank after shebang
    new += doc
    if j < len(lines):
        new.append("")
    new += lines[j:]
    return "\n".join(new) + "\n"


def insert_prefixed(text: str, block: list[str], after_fence: bool = False) -> str:
    lines = strip_block(text.splitlines())
    if after_fence and lines and lines[0].strip() == "---":
        return "\n".join([lines[0]] + block + lines[1:]) + "\n"
    return "\n".join(block + ([""] if lines and lines[0].strip() else []) + lines) + "\n"


def apply(path: Path, rel: str) -> bool:
    links = link_set(rel)
    if not links:
        return False
    body = grouped_lines(links)
    text = path.read_text()
    suffix = path.suffix
    if suffix == ".py":
        new = insert_py(text, body)
    elif suffix == ".astro":
        new = insert_prefixed(text, block_c_comment(body), after_fence=True)
    elif suffix in (".ts", ".js"):
        new = insert_prefixed(text, block_c_comment(body))
    elif suffix == ".svelte":
        new = insert_prefixed(text, block_html_comment(body))
    elif suffix in (".yaml", ".yml") or path.name in ("compose.yaml",):
        new = insert_prefixed(text, block_hash_comment("#", body))
    elif suffix in (".html", ".htm"):
        if rel.startswith("backend/"):
            new = insert_prefixed(text, block_django_comment(body))
        else:
            new = insert_prefixed(text, block_html_comment(body))
    else:
        return False
    if new != text:
        path.write_text(new)
        return True
    return False


def iter_files():
    excl = set(MANIFEST["exclude_dirs"])
    for root in MANIFEST["roots"]:
        p = REPO / root
        if p.is_file():
            yield p, root
            continue
        for f in p.rglob("*"):
            if not f.is_file():
                continue
            if any(part in excl for part in f.parts):
                continue
            if f.stat().st_size == 0:
                continue
            if f.name.endswith(".d.ts"):  # triple-slash directive must stay line 1
                continue
            rel = f.relative_to(REPO).as_posix()
            if link_set(rel):
                yield f, rel


def write_codemap(index: dict[str, list[str]]):
    lines = [
        "---", "title: CODEMAP", "type: reference", "status: active",
        "created: 2026-07-14", "tags: [harness, codemap, generated]", "---", "",
        "# CODEMAP — doc → code index",
        "",
        "> [!warning] Generated file",
        "> Regenerated by `.claude/skills/kdx-live-doc/link.py` from each code file's live-doc block. "
        "Do not hand-edit; edit the block (or the manifest) and re-run. Ruled by [[adr-17-live-doc-backlinks]].",
        "",
        "Each heading is a live-doc SSOT; the list is every code file that declares itself governed by it.",
        "",
    ]
    for doc in sorted(index, key=lambda d: (not d.startswith("adr-"), d)):
        lines.append(f"## [[{doc}]]")
        lines.append("")
        for rel in sorted(index[doc]):
            lines.append(f"- `{rel}`")
        lines.append("")
    (REPO / "docs" / "CODEMAP.md").write_text("\n".join(lines))


def main():
    check = "--check" in sys.argv
    changed, scanned = [], 0
    index: dict[str, list[str]] = {}
    for f, rel in iter_files():
        scanned += 1
        for lk in link_set(rel):
            index.setdefault(lk, []).append(rel)
        if check:
            before = f.read_text()
            if apply(f, rel):
                changed.append(rel)
                f.write_text(before)  # revert in check mode
        else:
            if apply(f, rel):
                changed.append(rel)
    if not check:
        write_codemap(index)
    print(f"scanned={scanned} changed={len(changed)} docs_indexed={len(index)}")
    for c in changed:
        print("  ~", c)
    if check and changed:
        sys.exit(1)


if __name__ == "__main__":
    main()
