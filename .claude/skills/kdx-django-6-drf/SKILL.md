---
name: kdx-django-6-drf
description: >
  Opinionated Django 6 + DRF backend entrypoint. Use when the user invokes
  kdx-django-6-drf, or works on Django/DRF models, viewsets, serializers,
  HTMX HTML fragments, migrations, pytest for the API, local Postgres-in-Docker,
  or ECS Fargate + RDS Postgres. Django 6 only — no older majors, no retrocompat
  shims.
metadata:
  version: "6.1b1"
  stack:
    django: "6.1b1"
    django_fallback: "6.0.7"
    djangorestframework: "3.17.1"
    python: "3.14.6"
    psycopg: "3.3.4"
    postgresql: "17.9"
    uv: "required"
  docs_as_of: "2026-07-10"
  template_ref: "~/Templates/astro-drf-aws"
  pins_ssot: "docs/REQUIREMENTS.md"
---

# kdx-django-6-drf

**Swiss-army Django API skill.** Trigger on `kdx-django-6-drf` or any Django/DRF backend work for kodex projects. Always assume this stack; do not invent alternatives.

## Fixed stack (no retrocompat)

| Layer | Choice |
|-------|--------|
| Framework | **Django 6.1b1** (template pin); fallback **6.0.7** stable if beta blocks — never invent a third number |
| API | **DRF** viewsets + routers (plain `APIView` only when a viewset does not fit) |
| OpenAPI | **drf-spectacular** (schema is derivative; `docs/API.md` is SSOT) |
| DB | **PostgreSQL 17.9** via **psycopg 3** — never SQLite for app data |
| Toolchain | **`uv` only** — never `pip` / poetry / pipenv |
| Server | **ASGI** on port **8000** (gunicorn+uvicorn workers or uvicorn; pin in REQUIREMENTS) |
| Cache | **`DatabaseCache`** (+ optional `LocMemCache` alias). **Redis / ElastiCache forbidden** |
| Tasks | **`django.tasks`** first. Celery only if the user explicitly demands it |
| Hypermedia | **HTMX fragments** — Django templates/`TemplateResponse` are the HTML producer; Astro only loads the client (`docs/HTMX.md`) |
| Frontend pair | Astro 7 SSR → skill `kdx-astro-7` (attributes + shell; not fragment HTML) |

**Pin SSOT:** project `docs/REQUIREMENTS.md` (template: `~/Templates/astro-drf-aws`). Metadata above mirrors that file — on re-pin, update REQUIREMENTS first, then this frontmatter. Prefer live PyPI / Django docs when versions drift mid-session. **Never** support Django ≤5.

## Only two runtimes

| Target | Database | How code differs |
|--------|----------|------------------|
| **Local** | Postgres 17 in Docker (or native 17) | Same app code; only env (`DB_*` vars, secrets) changes |
| **AWS** | RDS Postgres 17 + **ECS Fargate** task | Same app code; secrets from Secrets Manager; ASGI :8000 behind ALB |

Code **must not** branch on environment names. Settings are **fully env-driven** — no `settings/dev.py` / `settings/prod.py` splits.

Template infra SSOT: `~/Templates/astro-drf-aws/docs/` (`BACKEND`, `HTMX`, `BD`, `API`, `TDD`, `CACHE`, `INFRASTRUCTURE`, `VARIABLES`, `REQUIREMENTS`).

## Forbidden (reject unless user overrides in-turn)

- Django 5.x / 4.x patterns, LTS “support matrices”, version-gated shims
- `CheckConstraint(check=…)` → use **`condition=`** (Django 5.1+; required on 6)
- `DEFAULT_FILE_STORAGE` / `STATICFILES_STORAGE` → use **`STORAGES`**
- `django-csp` as primary CSP → use **`ContentSecurityPolicyMiddleware` + `SECURE_CSP`**
- `SECURE_BROWSER_XSS_FILTER` cargo-cult (browsers ignore it)
- Redis / ElastiCache / celery-as-default
- `pip install`, requirements.txt-only workflows when `uv` is available
- JSON:API / Prowler-style multi-tenant RLS scaffolding (not our default)
- `trailing_slash=False` (we keep **trailing slashes**)
- `fields = "__all__"` / `exclude = …` on serializers
- Business logic in serializers or views (use services / model methods / managers)
- Routes not declared in `docs/API.md`
- Domain HTML fragments rendered by Astro/Svelte for HTMX swaps (Django owns fragment HTML)
- Returning JSON from a route that HTMX is expected to swap without an explicit dual-contract design
- Manual SQL schema / non-Django migration tools
- Non-English comments, docstrings, or log messages ([[LOCALIZATION]])

## Non-negotiables

1. **English only** in code, identifiers, comments, and docstrings ([[LOCALIZATION]]). Prefer no comments (KISS); never non-English.
2. **DRY / KISS / extreme minimal.** No dead wrappers, no “just in case”.
3. **Workflow:** `plan → docs/API.md row → TDD → models.py → rest of DRF` (JSON) or fragment views/templates. No model/endpoint without an API row.
4. **HTMX from day one** when the feature is server-owned interactive: plan partial templates, CSRF, session auth, HTML errors, and `HX-*` response headers *with* the API row — not as a retrofit. Doctrine: `docs/HTMX.md`.
5. **Single Django project**; one app per domain. No grab-bag `core`/`utils` apps.
6. **Migrations are the only schema mechanism.**
7. **ORM always** for queries; raw SQL only parameterized and justified.
8. **Secrets:** env locally (gitignored); **AWS Secrets Manager** on Fargate. Never commit secrets.
9. **Authenticated responses** default `Cache-Control: no-store` unless the API row says otherwise.

## Django 6 — use these, not the old thing

| Do | Don’t |
|----|--------|
| `CheckConstraint(condition=Q(…), name="…")` | `check=` |
| `STORAGES = {"default": …, "staticfiles": …}` | `DEFAULT_FILE_STORAGE` / `STATICFILES_STORAGE` |
| `SECURE_CSP` + `ContentSecurityPolicyMiddleware` | third-party CSP middleware as default |
| `@task` / `django.tasks` backends | Celery by reflex |
| `GeneratedField` / `db_default` when useful | always-compute-in-Python columns |
| Python **3.14.6** (REQUIREMENTS pin) | Python 3.10–3.13 “because it still works” |

## DRF doctrine (ultra-short)

Load recipes: `references/patterns.md`.

| Rule | Detail |
|------|--------|
| Serializers | **Split by action:** `XSerializer` (read), `XCreateSerializer`, `XUpdateSerializer` |
| Fields | Explicit whitelist only; system fields `read_only` |
| ViewSets | Default; `get_queryset()` always applies `select_related` / `prefetch_related` |
| spectacular | Guard `if getattr(self, "swagger_fake_view", False): return qs.none()` |
| Filters | `filterset_class` for anything non-trivial (not only `filterset_fields`) |
| Permissions | Class on the viewset; object-level when ownership matters |
| OpenAPI | `@extend_schema_view` / `@extend_schema_field` on method fields |
| Errors | Generic messages; prefer 404 over 403 when it prevents enumeration |
| Prefixes | Backend paths under `/api/`, `/admin/`, `/accounts/`, `/ws/` only |
| HTMX | Fragment routes return `text/html`; serializers column is `—` in API.md; tests assert status + key markup |

## HTMX fragments (Django produces HTML)

HTMX is in the stack **because this backend exists**. Design fragment support when the feature needs server-owned UI — same cycle as any endpoint.

| Do | Don’t |
|----|--------|
| `TemplateResponse` + app templates | Expect Astro to emit domain swap HTML |
| Separate API.md rows for JSON vs HTML | One JSON view “also used” as HTMX without a row |
| CSRF + session for mutating `hx-*` | Token-only SPA defaults for browser forms |
| HTML validation / permission error fragments | Bare JSON error body for HTMX targets |
| Stable element ids matching `hx-target` | Ad-hoc ids only in the frontend shell |
| Outbound `HX-Trigger` / `HX-Redirect` / … when needed | Silent full-page assumptions |

Recipes: `references/patterns.md` → section HTMX.

## Layout (default)

```
config/                 # project package: settings.py, urls.py, asgi.py
apps/<domain>/          # models, serializers, views, urls, services, tests
apps/<domain>/templates/<domain>/   # HTMX partials live with the domain
manage.py
pyproject.toml          # uv
docs/API.md             # endpoint SSOT (JSON + HTML fragments)
docs/tdds/              # TDD entries when the project uses them
```

## Testing

- **pytest + pytest-django** via `uv run pytest`.
- DB: real Postgres when integration matters; never invent a second production engine.
- Factories OK (`factory_boy`); no fixture sprawl.
- Cover permissions, validation, and queryset/N+1 hotspots — not Django internals.

## Agent ops

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000   # or project ASGI entry
uv run pytest -x --tb=short
uv run python manage.py spectacular --file schema.yml   # if spectacular configured
```

Fargate: container listens **8000**, health on declared `/api/health/` (or project health path). Image built once; env/secrets select local vs RDS.

## Retrieval

| Topic | Source |
|-------|--------|
| Django 6.1 | https://docs.djangoproject.com/en/dev/ · release notes `/releases/6.1/` · stable 6.0 docs if beta pages lag |
| CSP | https://docs.djangoproject.com/en/dev/ref/middleware/#content-security-policy |
| Tasks | https://docs.djangoproject.com/en/dev/topics/tasks/ |
| DRF | https://www.django-rest-framework.org/ |
| spectacular | https://drf-spectacular.readthedocs.io/ |
| Pins | project `docs/REQUIREMENTS.md` |
| Template | `~/Templates/astro-drf-aws/docs/BACKEND.md` · `HTMX.md` · `API.md` · `BD.md` · `TDD.md` · `CACHE.md` |
| HTMX client | https://htmx.org/docs/ · pin `htmx.org` in REQUIREMENTS |

On demand: `references/patterns.md`.
