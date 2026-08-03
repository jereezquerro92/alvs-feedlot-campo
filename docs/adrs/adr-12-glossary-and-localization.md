---
title: adr-12-glossary-and-localization
type: adr
category: harness
use_case: naming anything new — a model, field, enum value, service, route, env var, i18n key — or finding one thing called two different ways
created: 2026-07-10
modified: 2026-08-02
tags: [adr, glossary, localization, naming]
---

# ADR-01 — glossary and localization

## CONTEXT

> Spanish and English are both allowed. Two names for one thing are not. [[GLOSSARY]] records which name won, and the loser becomes a forbidden form.

## ASSERTIONS

1. A name is decided in [[GLOSSARY]] before its first use. Every identifier-worthy term — model names, endpoint segments, env var stems, service names, UI labels, doc names — uses the canonical form registered there. A new term gets its row first; the ABC gate ([[AGENTS]]) applies to naming like to everything else.
2. A term's row carries its rejected synonyms in the Forbidden forms column. That column is where duplicity is settled: once a name wins, every other name for the same thing is forbidden, in whichever language it was written.
3. A name may be Spanish or English. Which language a term uses is decided once, per term, and the choice binds every later use of it. Neither language is the default and neither needs a justification; only a second name for an already-named thing does.
4. One term, one language, all the way down. A name decided for a concept is the name its model, fields, service functions, serializers, routes, metrics, env stems and i18n keys all use. A Spanish word inside an otherwise-English identifier is two conventions in one name, and rule 2 settles it like any other duplicity.
5. A naming question resolves in [[GLOSSARY]]; a language, locale or rendering question resolves in [[LOCALIZATION]].
6. Two bilingual pairings are sanctioned conventions, not violations, because each has exactly one canonical form and one rendering of it:
   - a `TextChoices` member stores an English key and displays a Spanish label — `COW = "cow", "Vaca"`. The stored value is the name; the label is rendering;
   - an i18n message uses an English `snake_case` key and a Spanish value in `frontend/src/i18n/messages/`. The key is the name; the value is rendering.

   Anything a user reads that is neither of these — a label hardcoded in a component, a message generated server-side, a string built into a persisted field — has no canonical form and is a defect.
7. Every divergence found between the code and this ADR resolves exactly one of two ways, and both are recorded: the name is **registered** in [[GLOSSARY]] as the canonical form, or an **issue** is opened to correct the code to the name that already won. Finding a divergence and doing neither is how the project acquired the ones it has.

## FORBIDDEN

- **NEVER** give one concept two names (rule 2). `PUBLIC_API_URL` and `PUBLIC_BACKEND_URL` were both declared as the client-visible backend URL, and neither row said which was which. Rule 7 settled it: `PUBLIC_BACKEND_URL` — the only one any code read — is registered in [[GLOSSARY]], and the phantom was dropped from [[VARIABLES]], `.env.example`, `env.d.ts`, `compose.yaml` and the deploy workflow.
- **NEVER** name a thing that already has a name instead of reading its row (rule 1). The near-miss is the instructive one: `ear_tag` and `Caravana` look like one concept named twice and are not — [[GLOSSARY-feedlot-additions]] separates the internal identifier from the official SENASA record, each forbidding the other's name. The rows settled it; a reader who skipped them would have "fixed" a distinction the project needs.
- **NEVER** put a foreign stem inside an otherwise-consistent identifier (rule 4). `engorde_commission_pct` (`backend/apps/livestock/models.py:235`) names in Spanish the same gain that `kilos_gained` names in English.
- **NEVER** let the same class of message pick its language by when it was written (rule 4). `ValidationError` messages are Spanish in the Phase 2–7 apps and English in `breeding`, `genetics` and `traceability` — a split no decision ever made.
- **NEVER** hardcode a label a message key already carries (rule 6). Around ten components hold local `Record<string, string>` maps of Spanish enum labels, several duplicating keys that exist in `messages/es.ts` and are used correctly elsewhere in the same codebase.
- **NEVER** generate user-facing text server-side and persist it (rule 6). Nine `LedgerEntry.description` call sites write Spanish prose into the database, where no i18n key can reach it and no translation can ever change it.

## REJECTED

- **English-only code** — rules 3 and 4 until 2026-08-02 read "everything that is code is English — always, no exceptions" and "non-English text exists ONLY in the frontend's rendered output". Retired by the owner in conversation. It lost because it was never true and its untruth was invisible: the project has 20 Spanish ADRs, 18 Spanish domain documents, 45 enums with Spanish labels, 9 apps with Spanish admin names and a Spanish-speaking advisor by design — all of it working, none of it a defect anybody wanted fixed. A rule the codebase contradicts in hundreds of places stops being enforced and starts being ignored, and an ignored rule hides the real defect standing beside it, which is duplicity. Naming one language the winner was never the goal; naming one form per thing is. It would reopen only if this project stopped being read and operated in Spanish.
- **Registering a term per language** — a row for the English name and a row for the Spanish one, cross-referenced. It would have described the codebase accurately and made the collisions permanent: two valid names for one thing is the exact condition rule 2 exists to end. Closed while rule 2 stands.

## RELATED

### related adrs

- [[docs/adrs/adr-00-discipline]] — the shape this ADR is written in, and rule 8 under which its policy changed
- [[docs/adrs/adr-24-feedlot-domain]] — stages the feedlot's new names before first use

### related files

- [[docs/GLOSSARY]] — the naming authority; 291 registered terms
- [[docs/GLOSSARY-feedlot-additions]] — where the feedlot domain's terms are staged
- [[docs/constitution/LOCALIZATION]] — rendering, locale and the i18n mechanism
- [[docs/VARIABLES]] — env var names, bound by rules 1–4 like any other identifier
- [[AGENTS]] — the ABC gate rule 1 invokes
- [[docs/COMPONENTIZATION]] — cites rule 1 as the reason component names are decided in [[GLOSSARY]], not there
