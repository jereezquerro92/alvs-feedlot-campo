---
name: kdx-astro-7
description: >
  Opinionated frontend entrypoint for Astro 7 + Svelte 5 + HTMX. Use when the
  user invokes kdx-astro-7, mentions Astro, .astro, Svelte islands, HTMX,
  Melt UI, or shadcn-svelte UI work. The only interaction tools are Svelte and
  HTMX; anything else requires explicit user justification.
metadata:
  version: "7.0.7"
  stack:
    astro: "7.0.7"
    svelte: "5.56.4"
    "@astrojs/svelte": "9.0.1"
    htmx: "2.0.10"
    melt: "^0.44.0"
    shadcn_svelte_cli: "1.4.1"
  docs_as_of: "2026-07-15"
  template_ref: "~/Templates/astro-drf-aws"
---

# kdx-astro-7

**Swiss-army frontend skill.** Trigger on `kdx-astro-7` or any Astro mention. Always assume this stack; do not invent alternatives.

## Fixed stack (no retrocompat)

| Layer | Choice |
|-------|--------|
| Framework | **Astro 7 only** (latest) |
| UI language | **Svelte 5 only** (`@astrojs/svelte` v9+) — always present |
| Hypermedia | **HTMX 2** (`htmx.org@2.0.10`) — in stack; **Django** generates fragment HTML |
| Components | **Melt UI** builders (`melt/builders`) first, **shadcn-svelte** CLI second (owned source) |
| Design system | **Agnostic** — Melt/shadcn-svelte are the foundation/distribution; tokens, brand, and theme are project-owned |

Pinned with **bun** (2026-07): `astro@7.0.7` · `svelte@5.56.4` · `@astrojs/svelte@9.0.1` · `htmx.org@2.0.10` · `melt@^0.44.0` · `shadcn-svelte@1.4.1`. Prefer live docs / MCP when versions drift.

**Toolchain:** `bun` only — package manager, runtime, and lockfile (`bun.lock`). **npm / npx / pnpm / yarn are prohibited.** Use `bun add`, `bun run`, `bunx`. Reference architecture: `~/Templates/astro-drf-aws` (`docs/FRONTEND.md`, `docs/HTMX.md`).

## Only two interaction options

The agent may choose **only**:

1. **Svelte** — components (SSR by default) and islands when client state is real  
2. **HTMX** — HTML-over-the-wire for server-owned dynamic UI; **fragment bodies come from Django**, not from Astro/Svelte  

**Everything else is forbidden unless the user explicitly justifies it in the current request** (name the alternative and why). That includes React, Vue, Solid, Alpine, hand-rolled `<script>` UI, other component kits, SPA routers, and generative-UI packages (e.g. json-render).

### Interactivity ladder (never skip)

```
1. Server-rendered HTML (Svelte SSR, no client:*) + CSS
2. HTMX (hx-*) — Django owns state + fragment HTML; Astro places hx-*
3. Svelte island (leanest client:*) — client owns state
```

| Signal | Use |
|--------|-----|
| Forms, submit-and-refresh | HTMX |
| Lists, pagination, filters | HTMX |
| Partial region refresh / polling | HTMX |
| Local widget state, optimistic UI | Svelte island |
| Offline / pointer-heavy / canvas | Svelte island |

When in doubt: stay lower on the ladder.

## Non-negotiables

1. **English only** in code, identifiers, comments, and docstrings ([[LOCALIZATION]] / template docs). Prefer no comments (KISS); never non-English. Product copy may be localized at render time.
2. **DRY / KISS / extreme minimal.** No dead wrappers, no “just in case”.
3. **bun only** for install, run, scripts, tests, lockfile, and container runtime (`oven/bun`). Never `npm` / `npx` / `pnpm` / `yarn`.
4. **Only routes and layouts are `.astro`; everything else is `.svelte`.** `@astrojs/svelte` is mandatory. This includes static text pieces like a page `<title>` — those are a zero-hydration `.svelte` component (no `client:*`, no runtime shipped), never markup authored inline in `.astro`. A title is UI, not composition. `.astro` stays limited to thin routes, layouts, data fetch, and composing `.svelte` children.
5. **Component layer, in order: Melt UI builder → shadcn-svelte → hand-rolled.** Reach for a Melt builder (`melt/builders`) first — headless, full control over markup and behavior, the default posture for any new UI piece (`references/melt-ui.md`). Fall to shadcn-svelte via CLI (`add`) only when the need is a standard, pre-built shape a builder would just reinvent. Hand-rolled markup outside both is the last resort and needs the same explicit justification as any other forbidden pattern. Never invent a parallel kit; customize tokens/theme in either layer, do not replace the foundation.
6. **Svelte 5 runes only** (`$state` `$props` `$derived` `$effect`). No Svelte 3/4 APIs.
7. **Astro 7 compiler rules:** close tags; JSX whitespace; Sätteri Markdown; no `@astrojs/db`; top-level `cache`/`logger`/`routeRules`.
8. Prefer **zero client JS**. SSR Svelte without `client:*` ships no Svelte runtime.
9. **HTMX client only on the frontend.** Load `htmx.org` once in the layout. Domain fragment HTML is produced by Django (`docs/HTMX.md`, skill `kdx-django-6-drf`). Do not implement swap bodies in Astro/Svelte.
10. **Units: rem over px, hex over OKLCH only for a fixed literal.** Spacing and sizing are always `rem` (Tailwind's spacing scale already is — never hand-write a `px` value). A one-off, non-tokenized literal (e.g. a decorative shadow color) is `hex`; anything token-backed goes through `app.css`'s OKLCH token layer (`docs/DESIGN-SYSTEM.md`) — never author a token in hex or rgb.

## Agent toolchain (this machine)

| Tool | Role |
|------|------|
| **This skill** | Entry doctrine + layout + ladder |
| **Melt UI** (`melt` package, `melt/builders`) | Builder-first primitive layer — reach for it before shadcn when a piece needs full custom control (`references/melt-ui.md`) |
| **shadcn-svelte MCP** (`shadcn-svelte`) | Live component source/demos from huntabyte/shadcn-svelte — use when a vendored primitive already covers the need |
| **Astro Docs MCP** | `https://mcp.docs.astro.build/mcp` when available |
| **CLI** | `bunx shadcn-svelte@latest add <name>` to copy components into the project |

When building or modifying UI: **decide Melt vs shadcn first** (`references/melt-ui.md`), query the shadcn-svelte MCP only if a vendored primitive fits, add missing pieces with the CLI, then compose in Svelte.

## Retrieval

| Topic | Source |
|-------|--------|
| Astro 7 | https://docs.astro.build · upgrade https://docs.astro.build/en/guides/upgrade-to/v7/ |
| Svelte in Astro | https://docs.astro.build/en/guides/integrations-guide/svelte/ |
| Islands | https://docs.astro.build/en/guides/framework-components/ |
| Svelte 5 | https://svelte.dev/docs/svelte · https://svelte.dev/docs/svelte/$state |
| Melt UI | https://next.melt-ui.com/ (builders, Svelte-5 runes-native) |
| shadcn-svelte | https://www.shadcn-svelte.com/docs · Astro: …/docs/installation/astro |
| HTMX | https://htmx.org/docs/ |
| Template | `~/Templates/astro-drf-aws/docs/FRONTEND.md` · `HTMX.md` · `MELT-UI.md` |

Load on demand: `references/stack.md` · `references/patterns.md` · `references/svelte-5.md` · `references/melt-ui.md` · `references/shadcn-svelte.md`

## Scaffold

```bash
bun create astro@latest
bunx astro add svelte --yes
bunx astro add tailwind --yes
bun add svelte@latest @astrojs/svelte@latest htmx.org@2.0.10 melt@latest
bunx shadcn-svelte@latest init
bunx shadcn-svelte@latest add button
```

## Layout

```
src/pages/*.astro           thin routes
src/layouts/*.astro         document shell; HTMX once
src/components/**/*.svelte  all UI, incl. titles and Melt builder wrappers
src/lib/components/ui/      shadcn-svelte copies (typical)
src/lib/                    api, types, utils
components.json             shadcn-svelte config
```

## Backend (default assumptions)

- REST (**DRF** JSON): thin `src/lib/api`; serializable props into Svelte  
- **HTMX:** `hx-*` only against paths declared in `docs/API.md`; responses are Django HTML fragments — never invent domain fragment markup here  
- Webhooks: lean `src/pages/api/**` endpoints only when justified  


## Agent ops

```bash
bunx astro dev --host 0.0.0.0 --port 4321
curl -s http://localhost:4321/
bunx astro check && bunx astro build
```
