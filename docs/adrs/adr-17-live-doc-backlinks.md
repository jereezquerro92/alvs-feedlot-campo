---
title: ADR-17 — live-doc backlinks
type: adr
status: active
created: 2026-07-14
tags: [adr, harness, docs, linking]
---

# ADR-17 — live-doc backlinks in code

Rules only; the block name and mechanics live in [[GLOSSARY]] and [[HARNESS]]; the file→doc mapping lives in the linker manifest, never here ([[adr-00-adr-doctrine]] rule 1).

1. Every code file the manifest matches carries exactly one live-doc block ([[GLOSSARY]]: live-doc block) — a delimited region (`LIVE-DOC:START` … `LIVE-DOC:END`) wrapped in that file's native comment syntax, placed at the top of the file. A matched file without the block, or with more than one, is a defect.
2. The block holds wikilinks only — never information. It names the ADRs that govern the file and the docs those ADRs own, as `[[wikilinks]]`, and nothing else: no prose, no restatement of a rule, no explanation. A block that paraphrases a doc violates this ADR exactly as an ADR that inlines a fact violates [[adr-00-adr-doctrine]] rule 1.
3. The mapping of file → links is owned by the linker manifest, not by any code file or this ADR. Adding, narrowing, or widening a file's governance is an edit to the manifest followed by a re-run; a block hand-edited to disagree with the manifest is drift, corrected by re-running, never by amending the block.
4. `models.py`, `views.py`, `viewsets.py`, `serializers.py`, `urls.py`, and the permission classes additionally cite `[[API]]` — the one doc, beyond the ADRs, that the route surface answers to ([[adr-03-api-and-backend]]). No other file type cites [[API]] from its block.
5. The doc→code direction is generated, never hand-kept. `docs/CODEMAP.md` is produced by the linker from the blocks; it is not a source of truth and is not edited by hand. The block is the SSOT of a file's governance; CODEMAP is its inverse index.
6. The block never becomes a second SSOT. It duplicates no rule and grants no authority; where a block and a doc could be read to disagree, the doc wins ([[adr-00-adr-doctrine]]). Wikilinks in code do not produce Obsidian backlinks — CODEMAP is the graph, and the block is a greppable pointer for humans and agents reading the file.
7. The linker is the sanctioned path, vendored per [[adr-14-harness]] and listed in [[HARNESS]]. Applying or checking blocks runs it; blocks are not authored by hand. Its manifest and script are harness tooling, not doctrine.
