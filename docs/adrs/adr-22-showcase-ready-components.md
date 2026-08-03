---
title: adr-22-showcase-ready-components
type: adr
category: frontend
use_case: writing or vendoring a Svelte component, adding one to the gallery, wiring an action prop, editing the component-mount test
created: 2026-07-15
modified: 2026-08-02
tags: [adr, frontend, components, showcase]
---

# ADR-22 — showcase-ready components

## CONTEXT

> Every component mounts with no props and does nothing dangerous when it does. That is what lets one vendored component serve the gallery and a real page without a forked showcase copy.

## ASSERTIONS

1. Every frontend component supports invocation with zero props. Called with no inputs it renders a self-defined default or fallback state and does not throw. How it formats its own "no data" state is its own choice; erroring on an empty invocation is a defect whatever that choice is.
2. The one exemption is a component whose only valid invocation is as a context-bound child of a parent compound component — never bare, by any caller. It may throw on a bare mount, because that throw states the parent requirement it exists to enforce. The parent itself carries rule 1 with no exemption.
3. Both halves — the requirement and the exemption's exact membership — are enforced by `frontend/tests/component-mount.test.ts` and its `CONTEXT_BOUND` list ([[COMPONENTIZATION]]).
4. A component's default invocation performs no mutating action: with no caller-supplied wiring it issues no POST, PATCH or DELETE, no navigation carrying session or state side effects, and no write. A component capable of such an action takes it through an explicit prop or callback, and that prop defaults to a safe no-op or a clearly-labeled disabled affordance when the caller supplies nothing.
5. This adds a component contract to [[adr-04-frontend-and-design-system]] rule 9 and changes nothing else about how components are built or styled.

## FORBIDDEN

- **NEVER** ship a component that throws on a zero-prop mount unless it is in `CONTEXT_BOUND` (rules 1–3). The list is the exemption; anything outside it is a defect the mount test catches.
- **NEVER** let a component mutate anything on its default invocation (rule 4). The gallery mounts every component, and a default that writes turns a page view into an action.
- **NEVER** fork a showcase copy of a component (rule 4). The gallery composes the real components; a copy drifts from the one the app ships.
- **NEVER** default an action prop to anything but a no-op or a labeled disabled state (rule 4). A default that acts is the same hazard arriving through the caller's silence.

## REJECTED

- **Separate showcase variants of each component** — a `*.demo.svelte` beside every real one, free to hardcode data and stub actions. Rejected because the demo stops resembling the component the moment either changes, and the gallery then documents something that does not ship.
- **A standing pre-v1 in-place-edit override on this ADR** — an owner authorization, recorded here on 2026-07-15, letting rules 1–2 be reworded without supersession while the project stayed pre-v1. Dropped as redundant on 2026-08-02: [[adr-00-adr-doctrine]] rule 8 now makes in-place policy change the normal path for every ADR, with the owner's authorization given in the conversation where it happens.

## RELATED

### related adrs

- [[docs/adrs/adr-04-frontend-and-design-system]] — rule 9, the componentization rule this contract attaches to

### related files

- [[docs/COMPONENTIZATION]] — the folder structure, the gallery, the `CONTEXT_BOUND` list
- [[docs/FRONTEND]] — how components are built and tested
- [[docs/DESIGN-SYSTEM]] — what a component looks like once it mounts
