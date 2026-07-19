---
title: FRONTEND
type: reference
status: active
created: 2026-07-10
tags: [harness, frontend]
---

# FRONTEND

Rules for the frontend service: Astro SSR + Svelte islands, one of the two Fargate services defined in [[INFRASTRUCTURE]]. Exact versions live ONLY in [[REQUIREMENTS]].

## Stack

- Astro runs in full SSR mode: `output: 'server'` with the node adapter in standalone mode. The server listens on port 4321, bound to host 0.0.0.0 so the container is reachable inside the task network.

> [!warning] Every page renders through `layouts/Base.astro`
> `styles/app.css` (Tailwind + theme tokens) is imported by `Base.astro` only. A page that hand-rolls its own `<html>/<body>` instead of rendering through `Base.astro` loads zero CSS — every Tailwind class on it is inert, silently. Markup-string tests pass on such a page regardless, so this defect is invisible to the test suite; catching it needs actual visual verification, not just assertions on rendered HTML.
- Svelte provides islands of interactivity on top of server-rendered HTML. Islands are the exception, not the default — see the interactivity ladder below.
- **Svelte is the shipped island technology, and the only one** ([[adr-04-frontend-and-design-system]]). Astro's architecture would accommodate a React island later without a rewrite, should a future ADR add one — that is a possibility the architecture leaves open, not a capability shipped today. The interactivity ladder below stops at Svelte; any new island framework needs its own ADR and [[REQUIREMENTS]] row first.
- Styling is Tailwind 4 (via the Vite plugin, CSS-first configuration — no `tailwind.config.js`). Components come from shadcn-svelte, which copies source into the repo rather than installing a runtime dependency; copied components are then owned by this codebase.
- Every visual and component decision — including the current theming model — is owned by [[DESIGN-SYSTEM]].
- **`.astro` is routes and layouts only** — every other visual unit, titles included, is a `.svelte` component ([[adr-04-frontend-and-design-system]] r9). Rationale, folder tree, and layering are owned by [[COMPONENTIZATION]].
- Terminology for "island", "SSR", and "hypermedia" is owned by [[GLOSSARY]].

## Toolchain

bun is mandatory for everything ([[adr-04-frontend-and-design-system]]): install, run, scripts, tests, and the lockfile (`bun.lock`) all go through bun. **npm is PROHIBITED. Node is not part of the stack.** The SSR build runs under bun itself, and the container base image is `oven/bun`. Why: one runtime end to end removes a whole class of "works locally, breaks in the image" drift.

> [!note] Adapter caveat
> The Astro node adapter officially targets Node. bun compatibility is therefore re-verified on every Astro major upgrade. Node LTS is the documented fallback ONLY if a real incompatibility surfaces — never a convenience choice.

## Interactivity ladder

Escalate in order, never skip a rung ([[adr-04-frontend-and-design-system]]):

1. **Server-rendered HTML first.** Most pages need nothing else.
2. **[[HTMX]]** for dynamic fragments — hypermedia over the wire; **Django** returns the HTML (Astro only loads the client and places `hx-*`).
3. **A Svelte island** ONLY when genuine client-side state demands it.

Escalating this ladder is a per-feature decision made in [[BDD]]. Why: every rung up adds client-side complexity that the server cannot see or test.

HTMX is **in the stack** (pin in [[REQUIREMENTS]]). The client is bundled with bun and loaded once in the root layout. The HTMX-vs-Svelte decision criteria and the Django-as-producer doctrine are owned by [[HTMX]].

## Testing

- Frontend tests live HERE and are explicitly EXCLUDED from [[TDD]] — that flow is backend-only.
- The regime is laxer: tests are created per-feature as part of the [[BDD]] flow, using bun's built-in test runner.
- Coverage shape: component tests for Svelte islands, smoke tests for SSR routes. No more is required.

### Verification layers — `check` ≠ `build` ≠ `smoke`

Three distinct gates catch different failures; a change runs each where it applies, in this order:

1. **`bun run check`** (typecheck) — agent-run. Necessary but not sufficient: a green typecheck is not a buildable app.
2. **`bun run build`** (astro + rolldown production bundle) — agent-run, **headless, exit 0 required before merge**. It is the gate the Docker frontend image runs, so it must be green for the image to build. The production bundler rejects specifiers the typecheck accepts through `tsconfig` paths — e.g. a relative import at the wrong depth resolves under `tsconfig` but fails the bundle with `UNRESOLVED_IMPORT`. This layer is neither smoke nor `kodex`-only.
3. **Browser smoke** (chrome-devtools) — `kodex`-only and interactive ([[AGENTS]]); an agent that reaches a smoke step stops and defers.

## Server-side data access

- SSR code calls the backend via the internal service-discovery DNS name, never through the public ALB. Naming and networking conventions are owned by [[INFRASTRUCTURE]]. Why: looping traffic through the public edge adds latency, cost, and a dependency on public DNS for internal calls.
- The backend contract those calls consume is owned by [[API]].

## Browser-side data access

- Auth is the Django **session cookie** ([[AUTH]]), so every browser `fetch()` to the API MUST pass `credentials: 'include'` — without it the cookie is never sent and the API answers 401/403. The backend replies `Access-Control-Allow-Credentials: true` structurally (`CORS_ALLOW_CREDENTIALS = True` is a constant in settings, never an env toggle), because session auth makes credentialed CORS a consequence, not a choice.
- Unsafe methods (POST/PUT/PATCH/DELETE) additionally carry the CSRF token: read the `csrftoken` cookie (intentionally not `HttpOnly`) and send it as the `X-CSRFToken` header. The cookie/CSRF doctrine and the SameSite decision are owned by [[AUTH]].

## Environment

- The frontend receives ONLY public, non-secret variables, following the `PUBLIC_*` convention. No secrets ever reach this service — secrets live in AWS Secrets Manager and stay on the backend side. Variable names and their inventory are owned by [[VARIABLES]].

## Localization and caching

- Rendered text may be localized; all code, keys, and variables stay English. Rules in [[LOCALIZATION]].
- **Rendering context — the i18n layer.** `frontend/src/i18n/` is the catalog module: locale config (`config.ts`), one message file per locale under `messages/`, and a render helper `t(key, locale?)` exported from `i18n/index.ts`. A `.astro` page under `src/pages/` imports it with a relative path (`import { t } from "../i18n";`) and calls `t("some_key")` in its frontmatter or template. The output is a plain string — rung 1 of the interactivity ladder ([[adr-04-frontend-and-design-system]]): no client JS, no HTMX round trip, no island, just server-rendered text. Locale identity itself comes from Astro's native `i18n` config in `astro.config.mjs` (`defaultLocale`, `locales`), which also powers `Astro.currentLocale` and the `astro:i18n` helpers for any future locale-aware routing — the catalog module never re-implements URL/locale parsing itself.
- Caching of SSR responses follows [[CACHE]]. Redis is prohibited; [[CACHE]] owns all caching decisions.
