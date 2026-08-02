---
title: LOCALIZATION
type: reference
category: harness
use_case: choosing a language for a string, or adding an i18n message
created: 2026-07-10
modified: 2026-08-02
tags: [doc, harness, localization]
---

# LOCALIZATION

Simple and strict, following Django/DRF standard i18n. This doc owns all language and locale rules for both services ([[BACKEND]], [[FRONTEND]]).

## What this doc owns

Rendering, locale and the i18n mechanism. Which language a name uses is not decided here — it is decided once per term in [[GLOSSARY]] and binds every later use of it ([[adr-01-glossary-and-localization]] rules 1, 3–4). Spanish and English are both allowed; two names for one thing are not.

Two bilingual pairings are the sanctioned conventions, because each has one canonical form and one rendering of it ([[adr-01-glossary-and-localization]] rule 6): a `TextChoices` member stores an English key and displays a Spanish label (`COW = "cow", "Vaca"`), and an i18n message uses an English `snake_case` key with a localized value. Anything a user reads that is neither — a label hardcoded in a component, a message generated server-side, a string built into a persisted field — has no canonical form.

**Comments and docstrings:** prefer none (KISS — code should explain itself); [[BACKEND]] owns that posture. What is written follows the language its term was decided in.

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
