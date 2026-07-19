---
title: adr-04-frontend-and-design-system
type: adr
status: active
created: 2026-07-10
tags: [adr, frontend, design-system]
---

# ADR-04 — frontend and design system

Rules only; content lives in [[FRONTEND]] and [[DESIGN-SYSTEM]].

1. The frontend is Astro in full SSR mode with Svelte islands, as defined in [[FRONTEND]].
2. bun is mandatory for everything JavaScript — install, run, scripts, tests, lockfile, container runtime. npm is prohibited; Node is not in the stack ([[FRONTEND]], [[REQUIREMENTS]]).
3. The interactivity ladder is escalated in order, never skipping a rung: server-rendered HTML → [[HTMX]] → Svelte island. Escalation is a per-feature decision made in [[BDD]]; the HTMX-vs-Svelte criteria are owned by [[HTMX]].
4. Styling is Tailwind 4, CSS-first. Components come from shadcn-svelte and are vendored into the repo — once copied, this codebase owns them ([[FRONTEND]]).
5. Every visual and component decision is owned by [[DESIGN-SYSTEM]]. Where it conflicts with a component's shipped default, [[DESIGN-SYSTEM]] wins.
6. Frontend tests follow [[FRONTEND]] (bun test runner, per-feature via [[BDD]]) and are excluded from [[TDD]].
7. The frontend receives only `PUBLIC_*` variables, never secrets ([[VARIABLES]]).
8. Melt UI (pkg `melt`) is the headless builder layer beneath Bits UI and shadcn-svelte; Melt builders are the default sanctioned path for a new component, shadcn-svelte is reached for second, and a fully hand-rolled custom component is the last resort. Criteria for choosing Melt vs vendored shadcn-svelte vs custom are owned by [[MELT-UI]]; the variable-driven theming system (light/dark always) is owned by [[DESIGN-SYSTEM]].
9. Componentization: `.astro` files are routes and layouts only. A file under `src/pages/.astro` or `src/layouts/.astro` may compose other components and hold page-level wiring; it authors no non-trivial markup of its own. Every other visual unit — including a page's title — is a `.svelte` component, rendered with no hydration directive when it needs no client-side behavior. The folder structure, the componentization rationale, and the layer each component category resolves to are owned by [[COMPONENTIZATION]].
