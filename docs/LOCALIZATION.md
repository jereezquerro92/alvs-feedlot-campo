---
title: LOCALIZATION
type: reference
status: active
created: 2026-07-10
tags: [harness, localization]
---

# LOCALIZATION

Simple and strict, following Django/DRF standard i18n. This doc owns all language and locale rules for both services ([[BACKEND]], [[FRONTEND]]).

## The one rule

Everything that is code is English — always, no exceptions ([[adr-01-glossary-and-localization]]): identifiers, comments, docstrings, commit messages, API paths, env var names, test names, log messages. All English, everywhere, permanently. Why: agents and tooling read code as an index; a second language in code doubles the search space and breaks grepability.

**Comments and docstrings:** allowed only in English. Prefer none (KISS — code should explain itself). Do not ban comments as a hard rule; ban *non-English* and *noise*. When a future ADR requires docstring wikilinks ([[BACKEND]]), those docstrings are English too.

Non-English text is allowed ONLY in the frontend's rendered output. Even there, all variables, keys, and message IDs in code remain English; the target language exists solely at render time, through the i18n layer.

## Backend rule

- Django's standard machinery — `LANGUAGE_CODE`, `USE_I18N`, `gettext_lazy` — handles any user-facing string the API returns: validation errors, choices' labels. Nothing custom.
- DRF error messages follow the active locale. The endpoints that carry them are owned by [[API]].
- Framework configuration details beyond i18n belong to [[BACKEND]]; version pins to [[REQUIREMENTS]].

## Frontend rule

- Astro's native `i18n` config (`astro.config.mjs`: `defaultLocale`, `locales`) owns locale identity and routing primitives (`Astro.currentLocale`, `astro:i18n` helpers). No parallel translation mechanism is introduced — no i18next/paraglide/react-intl-shaped runtime enters [[REQUIREMENTS]]; the catalog below is hand-authored TypeScript, built directly on Astro's own primitives, per Astro's own documented i18n recipe.
- The message catalog lives at `frontend/src/i18n/` — locale config (`config.ts`: `defaultLocale`, `locales`, the `Locale` type), one catalog file per locale under `messages/` (e.g. `messages/es.ts`), and a single render helper `t(key, locale?)` exported from `i18n/index.ts`, defaulting to `defaultLocale` when no locale is passed.
- Translation catalogs are keyed in English: the key is the English message ID, the value is the localized string. Message IDs are `snake_case` (e.g. `lobby_pending`).
- The rendering context is defined in [[FRONTEND]].

## Default locale

- Owner decision (2026-07-14): this reference run's default locale is `es` (Spanish) — the first locale the i18n layer ships, backing the authorization-lobby `lobby_pending` message. It is a hardcoded constant (`defaultLocale` in `frontend/src/i18n/config.ts`, imported into `astro.config.mjs`'s `i18n.defaultLocale` — one SSOT, not two), not an environment-driven setting. A project forking this template re-decides its own default the same way, at the same seam, at its own project creation (the stage-3 project-construction point).
- Any locale-related setting that DOES become environment-driven (e.g. a future per-request or per-user locale override) is owned by [[VARIABLES]] before it is read — none exists today.

> [!note] Terminology
> "Locale", "message ID", and "catalog" are defined in [[GLOSSARY]].
