---
title: adr-53-api-membrane
type: adr
category: harness
use_case: writing or reviewing a frontend component or page that talks to the backend, editing docs/API.md, adding a live-doc block to a route file or a fetching component, reviewing a PR that adds a frontend fetch call
created: 2026-08-03
modified: 2026-08-03
tags: [adr, api, frontend, backend, membrane]
---

# ADR-53 — the API membrane

## CONTEXT

> `docs/API.md` is not a catalogue the backend keeps for its own convenience. It is the only point of contact between the two sides: the backend is obliged to publish everything it serves there, and the frontend is forbidden to know anything about the backend that is not there. Neither side may reach past it to look at the other.

## ASSERTIONS

1. The backend's half of the membrane is the publication obligation [[adr-51-api-and-backend]] rule 1 already owns: an endpoint is valid if and only if it is declared in [[API]]. This ADR does not restate that rule; it adds the symmetric half the pair needed and did not have.
2. The frontend's half is a prohibition of knowledge: no frontend file may know, name, or assume anything about the backend beyond what a row in [[API]] declares. Forbidden knowledge is the framework (Django, DRF), the ORM, a model name, a serializer class, a viewset class, an app name, a migration, or any internal shape of how a route is implemented. Permitted knowledge is exactly what a row states: the method, the path, the request/response shape the row describes, and the base URL the frontend reaches it at.
3. The base URL is not a leak. `PUBLIC_BACKEND_URL` ([[VARIABLES]]) is how the frontend addresses the membrane, not a window past it — it names where the contract lives, not what implements it.
4. The link is enforced, not trusted on either side. [[adr-17-live-doc-backlinks]] rule 4 already requires the backend's route surface — `models.py`, `views.py`, `viewsets.py`, `serializers.py`, `urls.py`, the permission classes — to cite [[API]] in its live-doc block. This ADR extends the same citation duty to the frontend side: every frontend file that performs a fetch or names an endpoint carries a live-doc block citing [[API]], never the backend file that serves it.
5. A frontend comment, docstring, or identifier stating a backend internal — "the serializer for this endpoint," "the ViewSet handles," a Django app path — is a membrane breach regardless of whether the resulting request is correct. The breach is in what the file knows, not in what it sends.
6. The enforcement available today is a local hook and the two live-doc citation obligations of rule 4; neither is an inviolable barrier. A hook is a bypassable nudge, the same honest limit [[adr-19-issue-worktree-pr]] rule 4 states for the PR gate — the only backstop stronger than a nudge is one this template does not ship on its own.

## FORBIDDEN

- **NEVER** name a Django, DRF, ORM, serializer, viewset, model, or app-internal detail in frontend code, comments, or docs (rule 2). The frontend that knows the implementation can be broken by a refactor the membrane was supposed to absorb.
- **NEVER** write a frontend fetch or endpoint reference with no corresponding row in [[API]] (rule 2). A frontend call to an undeclared route is trusting an implementation nobody promised to keep.
- **NEVER** cite a backend file (`views.py`, `serializers.py`, `viewsets.py`, a model) from a frontend live-doc block or comment in place of [[API]] (rule 4). The frontend's citation is the contract, never the code that happens to implement it today.
- **NEVER** describe the hook or the citation duty as an unbypassable barrier in any document (rule 6). A control stated as stronger than it is stops being checked.

## REJECTED

- **Adding this as new rules on [[adr-51-api-and-backend]]** — the obvious home, since it already owns the backend's publication half. Rejected under [[adr-00-discipline]] rule 7: an ADR is attached to one theme, and adr-51's theme is the API contract and the backend that serves it. The frontend's prohibition of knowledge is a rule about the frontend and about the boundary itself, not about the backend — folding it in would make adr-51 own both sides of a line it only stands on one side of.
- **A frontend-only rule on [[adr-52-frontend-and-design-system]]** — the mirror of the option above, symmetric and equally wrong: the membrane is the relationship between the two sides, not a property of the frontend alone, and adr-52's theme is the client surface's own construction, not what it may know about its counterpart.

## RELATED

### related adrs

- [[docs/adrs/adr-51-api-and-backend]] — rule 1, the backend's publication obligation this ADR mirrors
- [[docs/adrs/adr-52-frontend-and-design-system]] — the frontend's own construction rules, which this ADR does not restate
- [[docs/adrs/adr-17-live-doc-backlinks]] — rule 4, the citation duty this ADR extends to the frontend side
- [[docs/adrs/adr-19-issue-worktree-pr]] — rule 4, the honest-limit precedent this ADR's rule 6 follows
- [[docs/adrs/adr-00-discipline]] — rule 7, why this stays its own theme instead of folding into adr-51 or adr-52

### related files

- [[docs/API]] — the membrane itself, the table both sides cite
- [[docs/FRONTEND]] — how the frontend is built, on the permitted side of the membrane
- [[docs/BACKEND]] — how the backend is built, on the other side
- [[docs/VARIABLES]] — `PUBLIC_BACKEND_URL`, the address that is not a leak
</content>
