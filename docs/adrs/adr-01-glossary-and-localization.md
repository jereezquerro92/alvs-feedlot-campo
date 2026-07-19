---
title: adr-01-glossary-and-localization
type: adr
status: active
created: 2026-07-10
tags: [adr, glossary, localization]
---

# ADR-01 — glossary and localization

Rules only; content lives in [[GLOSSARY]] and [[LOCALIZATION]].

1. A name is decided in [[GLOSSARY]] before its first use. Every identifier-worthy term — model names, endpoint segments, env var stems, service names, UI labels, doc names — uses the canonical form registered there. A new term gets its row first; the ABC gate ([[AGENTS]]) applies to naming like to everything else.
2. Forbidden forms listed in [[GLOSSARY]] are banned everywhere: code, docs, prose, commit messages.
3. Everything that is code is English — always, no exceptions: identifiers, comments, docstrings, commit messages, API paths, env var names, test names, log messages. Rationale and mechanics live in [[LOCALIZATION]].
4. Non-English text exists ONLY in the frontend's rendered output, through the i18n layer defined in [[LOCALIZATION]]. Keys, message IDs, and variables stay English even there.
5. Naming questions resolve in [[GLOSSARY]]; language and locale questions resolve in [[LOCALIZATION]]. Neither rule is restated elsewhere — link, don't repeat.
