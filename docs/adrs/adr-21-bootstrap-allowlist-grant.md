---
title: adr-21-bootstrap-allowlist-grant
type: adr
status: active
created: 2026-07-15
tags: [adr, auth, lobby, rbac, allowlist, bootstrap]
---

# ADR-21 — the bootstrap allowlist grant

Rules only; content lives in [[AUTH]], [[VARIABLES]], [[GLOSSARY]]. This ADR adds a named exception to [[adr-20-authorization-lobby]] rule 3; it supersedes nothing and narrows nothing else.

1. A second, bounded grant path exists: the env-driven bootstrap allowlist. `AUTH_BOOTSTRAP_ALLOWLIST` ([[GLOSSARY]], [[VARIABLES]]) names accounts whose `AccessRequest.role` is filled automatically in the shared login provisioning path, at first login and re-checked on every login. This is the exact precedent of the bootstrap superuser ([[adr-10-auth]] rule 8): an operator/deploy-time, owner-controlled exception — never self-service, since the requesting user cannot influence the value ([[AUTH]]).

2. The allowlist reuses the existing machinery and creates no parallel authority. It only pre-fills the same `AccessRequest.role` an admin would set by hand in `/admin/`; the `post_save` signal of [[adr-20-authorization-lobby]] rule 3 remains the sole path from the row to a Group membership, and enforcement still reads Django Groups only ([[adr-10-auth]] rules 1–2, unchanged).

3. The allowlist never overrides an admin. It fills `role` only while `role` is null; a role already granted — or later cleared and re-granted — through `/admin/` is authoritative. A pair naming a Group that does not exist is skipped with a logged warning: a config typo must never break login or mint a new Group.

4. Accounts arrive only through env/[[VARIABLES]], never through code. The variable's row enters [[VARIABLES]] before code reads it and its name enters [[GLOSSARY]] before first use ([[adr-01-glossary-and-localization]], [[adr-03-api-and-backend]] rule 7). The committed `.env.example` may carry only the local-dev seed (`dev@example.com`); real accounts live in each project's django secret. Hardcoding an account identifier anywhere in code or docs is a defect ([[PRD]] — the template stays account-agnostic).

5. This is a doctrine addition, not a reversal. Cognito remains authentication-only, RBAC remains exclusively Django Groups, the lobby boundary of [[adr-20-authorization-lobby]] rules 1–2 is untouched, and the bootstrap superuser exception is neither widened nor connected to this one. Any change to rules 1–3 is semantic and MUST supersede this ADR ([[adr-00-adr-doctrine]]).
