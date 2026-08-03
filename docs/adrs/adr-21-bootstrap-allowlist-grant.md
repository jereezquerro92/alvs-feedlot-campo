---
title: adr-21-bootstrap-allowlist-grant
type: adr
category: backend
use_case: bootstrapping access on a fresh environment, editing AUTH_BOOTSTRAP_ALLOWLIST, touching the login provisioning path or an AccessRequest role
created: 2026-07-15
modified: 2026-08-02
tags: [adr, auth, lobby, rbac, allowlist, bootstrap]
---

# ADR-21 — the bootstrap allowlist grant

## CONTEXT

> A fresh environment has no admin to grant the first role, so one bounded, operator-controlled path fills `AccessRequest.role` from an env variable. It pre-fills what an admin would type and creates no second authority.

## ASSERTIONS

1. `AUTH_BOOTSTRAP_ALLOWLIST` ([[GLOSSARY]], [[VARIABLES]]) names the accounts whose `AccessRequest.role` is filled automatically in the shared login provisioning path — at first login and re-checked on every login. It is the precedent of the bootstrap superuser ([[adr-10-auth]] rule 8): an operator- and deploy-time exception, never self-service, because the requesting user cannot influence the value.
2. The allowlist reuses the existing machinery and creates no parallel authority. It fills the same `AccessRequest.role` an admin would set by hand; the `post_save` signal of [[adr-20-authorization-lobby]] rule 3 stays the sole path from that row to a Group membership, and enforcement still reads Django Groups only ([[adr-10-auth]] rules 1–2).
3. The allowlist never overrides an admin: it fills `role` only while `role` is null. A role granted — or cleared and re-granted — through `/admin/` is authoritative. A pair naming a Group that does not exist is skipped with a logged warning, so a config typo can neither break login nor mint a Group.
4. Accounts arrive only through env and [[VARIABLES]], never through code. The variable's row enters [[VARIABLES]] before code reads it and its name enters [[GLOSSARY]] before first use ([[adr-01-glossary-and-localization]], [[adr-03-api-and-backend]] rule 7). The committed `.env.example` carries only the local-dev seed; real accounts live in each project's django secret.
5. Cognito remains authentication-only, RBAC remains exclusively Django Groups, the lobby boundary of [[adr-20-authorization-lobby]] rules 1–2 is untouched, and the bootstrap superuser exception is neither widened nor connected to this one.

## FORBIDDEN

- **NEVER** hardcode an account identifier in code or docs (rule 4). The template stays account-agnostic ([[PRD]]), and a real address committed once is committed forever.
- **NEVER** let the allowlist overwrite a role an admin has set (rule 3). The admin is the authority; the allowlist only fills a blank.
- **NEVER** create a Group from an allowlist entry (rule 3). A typo would mint a role nobody defined and grant it silently.
- **NEVER** let a bad allowlist entry break login (rule 3). It is skipped and logged; access provisioning is not the place to fail hard on a config typo.
- **NEVER** write a role into Django Groups from anywhere but the `post_save` signal (rule 2). One path from record to membership is what keeps the two in agreement.

## REJECTED

- **A self-service claim of the first role** — the first user to log in taking `admins`. Rejected because it is exactly the self-service grant [[adr-20-authorization-lobby]] rule 3 closed, and a race on it hands the project to whoever logs in first.
- **A second grant table for bootstrap accounts** — its own model, separate from `AccessRequest`. Rejected because it would create a second authority over roles; rule 2 keeps the one row and the one signal.

## RELATED

### related adrs

- [[docs/adrs/adr-20-authorization-lobby]] — rule 3, the `AccessRequest` row and the signal this reuses
- [[docs/adrs/adr-10-auth]] — rules 1–2 and the rule 8 bootstrap-superuser precedent
- [[docs/adrs/adr-03-api-and-backend]] — rule 7, a variable is declared before it is read
- [[docs/adrs/adr-01-glossary-and-localization]] — a name decided before first use

### related files

- [[docs/AUTH]] — the login provisioning path this hooks into
- [[docs/VARIABLES]] — the `AUTH_BOOTSTRAP_ALLOWLIST` row and where its value lives
- [[docs/GLOSSARY]] — the variable's name and the terms around it
