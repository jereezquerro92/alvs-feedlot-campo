# Stack install (Astro 7 + Svelte 5 + HTMX + shadcn-svelte)

Verified 2026-07-10. Prefer MCP + live docs over pins when they drift.

## Svelte 5 (always)

```bash
bunx astro add svelte --yes
bun add svelte@latest @astrojs/svelte@latest
```

`@astrojs/svelte@9` requires `astro@^7` and `svelte@^5.43.6`. Never install `@astrojs/svelte@5` (Svelte 3/4).

`svelte.config.js`:

```js
import { vitePreprocess } from '@astrojs/svelte';

export default {
  preprocess: vitePreprocess(),
};
```

`astro.config.mjs` (shape; match current Tailwind integration from `astro add tailwind`):

```js
import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';

export default defineConfig({
  integrations: [svelte()],
  site: 'https://example.com',
});
```

Template note (`astro-drf-aws`): full SSR uses `output: 'server'` + `@astrojs/node` standalone, **executed under bun** (image `oven/bun`). Never install or run with npm. Follow the project’s own config when present.

## HTMX

```bash
bun add htmx.org@2.0.10
```

Pin matches `docs/REQUIREMENTS.md`. Load **once** in the root layout (bundled, not CDN in production). Prefer attributes on markup over custom script.

Core: `hx-get|post|put|patch|delete` · `hx-target` · `hx-swap` · `hx-trigger` · `hx-indicator` · `hx-boost`.

**Doctrine (astro-drf-aws):** fragment **HTML is rendered by Django** (templates / `TemplateResponse`). Astro only ships the client and `hx-*` wiring. Do not build domain swap markup in Astro or Svelte. See `docs/HTMX.md` and skill `kdx-django-6-drf`.

## shadcn-svelte (component foundation)

Docs: https://www.shadcn-svelte.com/docs/installation/astro

```bash
bunx astro add tailwind --yes
bunx shadcn-svelte@latest init
bunx shadcn-svelte@latest add button
```

- Copies **source into the repo** (not a closed runtime dependency). Own and edit copies.
- Paths follow `components.json` (often `src/lib/components/ui`).
- **Design-system agnostic:** change CSS variables / theme freely; do not replace the foundation with another kit.
- Before writing a primitive: **shadcn-svelte MCP** → then `shadcn-svelte add`.

## Astro 7 hard constraints

| Rule | Action |
|------|--------|
| Unclosed tags | Build fails (Rust compiler) |
| Whitespace | JSX-like; use `{' '}` when needed |
| Markdown | Sätteri default |
| `src/fetch.ts` | Reserved advanced routing |
| `@astrojs/db` | Removed — never use |
| cache / logger / routeRules | Top-level only |

## Adapters / SSR

This template: **node adapter + bun runtime** only.

```bash
bunx astro add node --yes
```

Other adapters (`cloudflare`, `netlify`, `vercel`) only if the user overrides in-turn — still via `bunx`, never `npx`.

## MCP (this machine)

- **Name:** `shadcn-svelte`  
- **Command:** `~/MCP/bin/shadcn-svelte-mcp`  
- **Upstream:** `@jpisnice/shadcn-ui-mcp-server --framework svelte` → huntabyte/shadcn-svelte  
- Use for: list/search components, demos, source, dependencies  

Do not point this MCP at React mode for kdx-astro-7 work.
