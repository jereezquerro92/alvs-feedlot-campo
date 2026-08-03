---
title: adr-51-api-and-backend
type: adr
category: backend
use_case: adding or changing an endpoint, editing docs/API.md, writing a viewset/serializer/model, wiring a setting that reads an env var
created: 2026-07-10
modified: 2026-08-02
tags: [adr, api, backend]
---

# ADR-03 — API and backend

## CONTEXT

> An endpoint exists only where [[API]] says it does, and it is written before the line of code that serves it.

## ASSERTIONS

1. An endpoint is valid if and only if it is declared in [[API]]. No route may exist in code without its row; an undeclared route found in code is a defect, regardless of whether it works.
2. [[API]] is written before tests and before models: `plan → [[API]] → [[TDD]] → models.py → rest of DRF`.
3. The change protocol of [[API]] is binding: a row changes in its own reviewable act; removing an endpoint removes its row first, the code second; a row change invalidates the corresponding [[TDD]] entry in the same cycle.
4. HTMX fragment routes are endpoints and follow rule 1 ([[HTMX]], ruled by [[adr-05-htmx]]).
5. Backend service rules are owned by [[BACKEND]]: single Django project, one app per domain, env-driven settings, viewsets by default, ASGI on port 8000.
6. Once the base template is finished, all backend code is born through the [[TDD]] flow; the full loop is ruled by [[adr-07-development-flow]].
7. Every variable a setting reads is declared in [[VARIABLES]]; secrets come from AWS Secrets Manager only.

## FORBIDDEN

- **NEVER** write a route with no row in [[API]] (rule 1). A route that only exists in code is a route only its author knows about, until someone else finds it the hard way.
- **NEVER** write a model or a test before [[API]] carries the row (rule 2). The sequence exists so the contract is decided before the code built to serve it.
- **NEVER** change a row without updating its [[TDD]] entry in the same cycle (rule 3). A test suite that still describes the old contract passes for the wrong reason.
- **NEVER** read a setting from an env var absent from [[VARIABLES]] (rule 7). An undeclared variable is a config nobody can find without reading the settings file itself.

## RELATED

### related adrs

- [[docs/adrs/adr-05-htmx]] — fragment routes as a named case of rule 4
- [[docs/adrs/adr-07-development-flow]] — the API→TDD loop rule 6 defers to

### related files

- [[docs/API]] — the endpoint contract this ADR enforces
- [[docs/BACKEND]] — Django service rules owned there
- [[docs/VARIABLES]] — the variable inventory rule 7 requires
- [[docs/TDD]] — the flow rule 6 requires
