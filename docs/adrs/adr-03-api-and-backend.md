---
title: adr-03-api-and-backend
type: adr
status: active
created: 2026-07-10
tags: [adr, api, backend]
---

# ADR-03 — API and backend

Rules only; content lives in [[API]] and [[BACKEND]].

1. An endpoint is valid if and only if it is declared in [[API]]. No route may exist in code without its row; an undeclared route found in code is a defect, regardless of whether it works.
2. [[API]] is written before tests and before models: `plan → [[API]] → [[TDD]] → models.py → rest of DRF`.
3. The change protocol of [[API]] is binding: a row changes in its own reviewable act; removing an endpoint removes its row first, the code second; a row change invalidates the corresponding [[TDD]] entry in the same cycle.
4. HTMX fragment routes are endpoints and follow rule 1 ([[HTMX]], ruled by [[adr-05-htmx]]).
5. Backend service rules are owned by [[BACKEND]]: single Django project, one app per domain, env-driven settings, viewsets by default, ASGI on port 8000.
6. Once the base template is finished, all backend code is born through the [[TDD]] flow; the full loop is ruled by [[adr-07-development-flow]].
7. Every variable a setting reads is declared in [[VARIABLES]]; secrets come from AWS Secrets Manager only.
