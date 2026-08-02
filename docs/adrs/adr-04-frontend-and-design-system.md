---
title: adr-04-frontend-and-design-system
type: adr
category: frontend
use_case: building a page or component, choosing HTMX vs a Svelte island, adding a UI library, wiring PUBLIC_* env vars, deciding where non-trivial markup lives
created: 2026-07-10
modified: 2026-08-02
tags: [adr, frontend, design-system]
---

# ADR-04 — frontend and design system

## CONTEXT

> Astro SSR with Svelte islands, bun end to end, and an interactivity ladder climbed one rung at a time — never jumped.

## ASSERTIONS

1. The frontend is Astro in full SSR mode with Svelte islands, as defined in [[FRONTEND]].
2. bun is mandatory for everything JavaScript — install, run, scripts, tests, lockfile, container runtime. npm is prohibited; Node is not in the stack ([[FRONTEND]], [[REQUIREMENTS]]).
3. The interactivity ladder is escalated in order, never skipping a rung: server-rendered HTML → [[HTMX]] → Svelte island. Escalation is a per-feature decision made in [[BDD]]; the HTMX-vs-Svelte criteria are owned by [[HTMX]].
4. Styling is Tailwind 4, CSS-first. Components come from shadcn-svelte and are vendored into the repo — once copied, this codebase owns them ([[FRONTEND]]).
5. Every visual and component decision is owned by [[DESIGN-SYSTEM]]. Where it conflicts with a component's shipped default, [[DESIGN-SYSTEM]] wins.
6. Frontend tests follow [[FRONTEND]] (bun test runner, per-feature via [[BDD]]) and are excluded from [[TDD]].
7. The frontend receives only `PUBLIC_*` variables, never secrets ([[VARIABLES]]).
8. Melt UI (pkg `melt`) is the headless builder layer beneath Bits UI and shadcn-svelte; Melt builders are the default sanctioned path for a new component, shadcn-svelte is reached for second, and a fully hand-rolled custom component is the last resort. Criteria for choosing Melt vs vendored shadcn-svelte vs custom are owned by [[MELT-UI]]; the variable-driven theming system (light/dark always) is owned by [[DESIGN-SYSTEM]].
9. Componentization: `.astro` files are routes and layouts only. A file under `src/pages/.astro` or `src/layouts/.astro` may compose other components and hold page-level wiring; it authors no non-trivial markup of its own. Every other visual unit — including a page's title — is a `.svelte` component, rendered with no hydration directive when it needs no client-side behavior. The folder structure, the componentization rationale, and the layer each component category resolves to are owned by [[COMPONENTIZATION]].

## FORBIDDEN

- **NEVER** install with npm, pnpm or yarn, or run Node as a runtime (rule 2). bun is both package manager and runtime; a second lockfile is a second answer to what version is installed.
- **NEVER** skip a rung of the ladder — a Svelte island for state a server render or HTMX could already own (rule 3). Escalation is a decision made in [[BDD]], not a default reach.
- **NEVER** let a component's shipped default override [[DESIGN-SYSTEM]] (rule 5). A vendored component is owned by this codebase the moment it is copied in.
- **NEVER** let the frontend read a secret or a variable outside `PUBLIC_*` (rule 7). The frontend has no Cognito variables and no secrets, ever ([[AUTH]]).
- **NEVER** author non-trivial markup inside a `.astro` route or layout file (rule 9). Every visual unit beyond page wiring is a `.svelte` component.

## RELATED

### related adrs

- [[docs/adrs/adr-05-htmx]] — rung 2 of the ladder rule 3 escalates through

### related files

- [[docs/FRONTEND]] — Astro/Svelte/bun rules
- [[docs/DESIGN-SYSTEM]] — every visual and component decision
- [[docs/MELT-UI]] — Melt vs shadcn-svelte vs custom criteria
- [[docs/COMPONENTIZATION]] — folder structure and componentization rationale
- [[docs/REQUIREMENTS]] — the bun/npm/Node pins
- [[docs/VARIABLES]] — `PUBLIC_*` boundary
- [[docs/BDD]] — where the ladder escalation decision is made
- [[docs/TDD]] — what frontend tests are excluded from
