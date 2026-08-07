---
title: BACKEND
type: reference
category: backend
use_case: writing or changing Django 6 + DRF code
created: 2026-07-10
modified: 2026-08-07
tags: [doc, harness, backend]
---

# BACKEND

Rules for the Django/DRF service — one of the two Fargate services ([[INFRASTRUCTURE]]). The frontend counterpart is [[FRONTEND]].

## Stack ruling

- Django 6.x + DRF at the **very latest versions**; beta releases are acceptable. Exact pins live in [[REQUIREMENTS]] only — never repeat a version number here or in code comments.
- Python environment is managed with `uv`, never pip. Why: one lockfile, one resolver, reproducible on Fargate and dev alike.
- The service runs an ASGI server on port 8000, websockets-capable (`/ws/` prefix — routing in [[INFRASTRUCTURE]]). The server choice is pinned in [[REQUIREMENTS]].
- Git follows [[GH]]: feature work merges to `main`; production is `prod`.

## Async ([[adr-16-async-mandatory]])

- **The project stays async-capable at all times** — ASGI server, config and dependencies never block a view from being `async def` ([[adr-16-async-mandatory]] rule 1). A plain sync `def` view remains the default and needs no justification; a feature reaches for `async def` when it streams or does non-blocking I/O. The owner's reason for carrying the capability: results are meant to reach the browser as they arrive, not after the whole response is built.
- **Server-Sent Events is the default streaming mechanism**: an `async def` view returning `StreamingHttpResponse` over an async generator. No Django Channels, no channel layer, no new infrastructure — it rides the existing ASGI server and crosses the ALB like any other HTTP response.
- **WebSockets** are the reserved escalation at the `/ws/` prefix ([[adr-16-async-mandatory]] rule 3). ElastiCache Valkey is the Django shared cache ([[CACHE]]); adopting Channels / a channel layer for fan-out across Fargate tasks is a separate owner decision — Valkey alone does not authorize it.
- **Bedrock calls (the router's inference client) use `boto3` wrapped in `asgiref.sync_to_async`, not `aiobotocore`.** boto3 is already the project's one AWS SDK dependency ([[REQUIREMENTS]]); an async view calling it through `sync_to_async` gets the async signature without adding and maintaining a second, less mainstream AWS SDK. Revisit only if measured latency proves the thread-pool wrap is a real bottleneck — never assumed up front.

Once the base template is finished, ALL backend code is produced through the TDD flow ([[TDD]] → `docs/tdds/`), never written directly; a backend diff without a corresponding TDD entry is invalid ([[adr-07-development-flow]]).

## Settings philosophy

- Settings are **fully env-driven**: no environment-specific settings modules, no hardcoded values that differ between dev and prod.
- Env var names are owned by [[VARIABLES]] and are never named here ([[adr-51-api-and-backend]] rule 7).
- Secret values come from AWS Secrets Manager ([[adr-50-initial-stack]] rule 6); in production they are read from nowhere else.

## Cross-cutting rules (owners linked)

- A name is decided in [[GLOSSARY]] before its first use, and which language it uses is decided with it ([[adr-12-glossary-and-localization]] rules 1–4).
- Rendering, locale and the i18n mechanism are owned by [[LOCALIZATION]].
- Caching follows [[CACHE]] ([[adr-06-cache]]).
- Database rules (engine, migrations, data conventions) are owned by [[BD]].
- Endpoints are owned by [[API]] ([[adr-51-api-and-backend]] rule 1).
- **Code carries no comments.** Naming and structure carry the meaning; a comment or docstring is a defect unless it states something the code genuinely cannot say (e.g. a non-obvious external constraint). A docstring that restates a rule already owned by a project doc — [[CACHE]], [[VARIABLES]], [[GLOSSARY]], any ADR — is duplication that drifts; link the doc from the PR or issue, not from the code.

## Static files

- **Cloud:** `collectstatic` publishes into the image; the backend container serves them directly behind the ALB `/static/*` rule — no CDN, no S3 involved ([[INFRASTRUCTURE]], [[CACHE]]). Low volume by design: statics are admin + DRF browsable API only.
- **Local:** Django's DEBUG static serving via `manage.py runserver` is enough — nothing extra.
- Django statics exist for the admin and the DRF browsable API only. Frontend assets are Astro's own build pipeline ([[FRONTEND]]) and are never Django statics.

## HTMX — Django is the fragment engine

[[HTMX]] is in the stack because this backend exists. Hypermedia swaps require **HTML that Django renders**. Design for that from the first plan of any server-owned interactive feature — not after a JSON-only API is “done”.

- **Fragment responses** use Django’s template engine (`TemplateResponse` / partial templates under `apps/<domain>/templates/`). DRF serializers produce JSON for API clients; they are not the default body of an `hx-swap`.
- **Separate [[API]] rows** for JSON vs HTML fragment contracts when both exist for the same resource.
- **From day one**, plan: partial template `id`s, CSRF for mutations, session auth for browser HTMX, HTML validation errors, and outbound `HX-*` headers where needed. Full checklist: [[HTMX]].
- Prefer **dedicated fragment views** (or an early, explicit `HX-Request` branch) over bolting HTML onto a viewset as a late special case.
- Fragment endpoints enter through [[API]] then [[TDD]] like any other backend code.

## Bootstrap superuser

`bootstrap_admin` (management command, `apps/users/management/commands/bootstrap_admin.py`) idempotently creates or updates a `django.contrib.admin` superuser row from `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD` ([[VARIABLES]]), read directly via `os.environ`. It runs on every container boot ([[DOCKER]]'s equivalent in `backend/Dockerfile`, before the ASGI server starts) — safe to re-run: absent vars skip cleanly, present vars upsert the row and rotate its password.

This is orthogonal to `AUTH_DEV_MODE` and [[adr-10-auth]] rule 6: that rule bounds the DEBUG-only session/OIDC dev-login path, not a `django.contrib.admin` superuser row. A superuser is expected to exist in prod, so no deploy-time system check rejects this command's presence or output.

**The `/admin/` login field is `sub`, not email.** `User.USERNAME_FIELD = "sub"` ([[adr-10-auth]] rule 5), so the bootstrap row is keyed on the fixed constant `sub="bootstrap-admin"` — that constant, not `DJANGO_SUPERUSER_EMAIL`'s value, is what goes in the login form's first field. `DJANGO_SUPERUSER_EMAIL` only sets the row's `email` column for display/audit; it authenticates nothing.

On local Compose, `DJANGO_SUPERUSER_PASSWORD` in `.env` needs its literal `$` doubled (Compose's own `$$`→`$` interpolation applies to `.env` values) — a password containing `$$$` must be written as `$$$$$$` in `.env` or it silently truncates.

## Project layout

- A **single Django project**; one app per domain, named per [[GLOSSARY]]. No grab-bag `core`/`utils` apps growing by accretion.
- DRF viewsets + routers are the default for **JSON** APIs; plain `APIView` / class-based views for **HTML fragments** when that fits better than forcing a viewset.
- Per domain app: `templates/<app>/…` partials for HTMX; keep fragment markup next to the domain that owns it.
- API schema is generated by **drf-spectacular** for JSON; the generated schema is derivative — [[API]] remains the source of truth for **all** routes including fragments (spectacular may omit pure HTML views; the table still lists them).
- Test discipline is [[TDD]].

> [!note] Forthcoming rule — docstring wikilinks
> `.py` files will adopt Obsidian-style wikilink references in docstrings (e.g. linking a viewset to its [[API]] row). Specification pending; it will be ruled by an ADR. Do not improvise a format before that ADR lands.
