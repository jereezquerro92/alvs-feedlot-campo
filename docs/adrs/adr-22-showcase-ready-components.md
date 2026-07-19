---
title: adr-22-showcase-ready-components
type: adr
status: active
created: 2026-07-15
tags: [adr, frontend, components, showcase]
---

# ADR-22 — showcase-ready components

Rules only; content lives in [[COMPONENTIZATION]], [[FRONTEND]], [[DESIGN-SYSTEM]]. This ADR adds a component-contract requirement to [[adr-04-frontend-and-design-system]]'s componentization rule; it narrows nothing else and supersedes nothing.

1. Every frontend component MUST support invocation with zero props. Called with no required inputs, it renders a self-defined default or fallback state and MUST NEVER throw. How a component formats its own "no data" state is its own choice; erroring on an empty invocation is a defect regardless of that choice. The one exemption is a component whose only valid invocation is as a context-bound child of a parent compound component — never bare, by any caller: it may throw on a bare mount, because that throw states the parent requirement it exists to enforce. The parent itself is bound by this rule with no exemption. Enforcement of both halves — the requirement and the exemption's named, exact membership — is `frontend/tests/component-mount.test.ts` and its `CONTEXT_BOUND` list ([[COMPONENTIZATION]]).

2. A component's default invocation MUST NEVER perform a mutating action. With no caller-supplied action wiring, a component MUST NOT issue a mutating API call (POST/PATCH/DELETE), a navigation with session/state side effects, or a DB write. Any component capable of such an action takes it only through an explicit prop or callback supplied by the caller, and that prop MUST default to a safe no-op — or a clearly-labeled disabled/demo affordance — when the caller does not supply it. This is what lets a vendored component be reused as-is in both the gallery and real app pages with no forked showcase copy ([[COMPONENTIZATION]] — gallery-only demo compositions are compositions of real components, not substitutes for them).

3. Owner override (2026-07-15, given in conversation): this ADR is a pre-v1 iteration surface. In-place edits to the wording of rules 1–2 — without supersession — are pre-authorized under [[adr-00-adr-doctrine]] rule 4(b) for as long as the project remains pre-v1, scoped to this ADR only. This grants no wider exception to [[adr-00-adr-doctrine]]'s supersession doctrine anywhere else.
