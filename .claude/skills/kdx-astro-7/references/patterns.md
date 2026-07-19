# Patterns (template-aligned)

Doctrine mirrors `~/Templates/astro-drf-aws/docs/FRONTEND.md` + `HTMX.md`.

## Thin page

```astro
---
import Layout from '../layouts/Base.astro';
import HomeView from '../components/home/HomeView.svelte';
import { getHome } from '../lib/api/home';

const data = await getHome();
---
<Layout title={data.title}>
  <HomeView {...data} />
</Layout>
```

No large markup in `.astro`. Compose Svelte only.

## Static Svelte (default)

```astro
---
import Card from '../components/Card.svelte';
---
<Card title="Hello" body="Static" />
```

No `client:*` → no client Svelte JS.

## HTMX (rung 2)

```svelte
<script lang="ts">
  let { action }: { action: string } = $props();
</script>

<button type="button" hx-post={action} hx-target="#result" hx-swap="innerHTML">
  Save
</button>
<div id="result"></div>
```

Fragment endpoints are real API surface — declare them; do not invent shadow routes.

## Svelte island (rung 3 only)

```astro
---
import Search from '../components/Search.svelte';
---
<Search client:visible endpoint="/api/search" />
```

Prefer `client:visible` / `client:idle`. Avoid blanket `client:load`. Use `client:only="svelte"` only when SSR is impossible.

## Melt builder (component layer, first choice)

```svelte
<script lang="ts">
  import { Toggle } from 'melt/builders';

  let { pressed = $bindable(false) }: { pressed?: boolean } = $props();

  const toggle = new Toggle({
    value: () => pressed,
    onValueChange: (v) => { pressed = v; },
  });
</script>

<button type="button" {...toggle.trigger}>{toggle.value ? 'On' : 'Off'}</button>
```

Reactive props as getters, attribute objects spread onto plain markup — full mechanics in `references/melt-ui.md`. Reach for a builder before shadcn whenever the piece needs full markup/behavior control.

## Titles are Svelte, not inline `.astro` markup

```svelte
<!-- src/components/PageTitle.svelte -->
<script lang="ts">
  let { text }: { text: string } = $props();
</script>

<title>{text}</title>
```

```astro
---
import PageTitle from '../components/PageTitle.svelte';
---
<PageTitle text={data.title} />
```

No `client:*` — zero-hydration static text, same as any other static Svelte piece. Never author `<title>{title}</title>` directly inside `.astro` markup.

## shadcn composition (second choice)

```svelte
<script lang="ts">
  import { Button } from '$lib/components/ui/button';
  import * as Card from '$lib/components/ui/card';

  let { title, body }: { title: string; body: string } = $props();
</script>

<Card.Root>
  <Card.Header>
    <Card.Title>{title}</Card.Title>
  </Card.Header>
  <Card.Content>
    <p class="text-sm text-muted-foreground">{body}</p>
  </Card.Content>
  <Card.Footer>
    <Button variant="secondary">OK</Button>
  </Card.Footer>
</Card.Root>
```

Reach for shadcn when the piece is a standard, pre-built shape a Melt builder would just reinvent. Add missing primitives: MCP inspect → `bunx shadcn-svelte@latest add <name>`.

## Units

- **rem over px** for spacing and sizing — Tailwind's own spacing scale already is rem; never hand-write a `px` value for a gap, padding, or width.
- **hex** for a fixed, one-off literal (a decorative value that will never vary by theme).
- **OKLCH** for anything token-backed — every entry in `app.css`'s token layer is OKLCH (`docs/DESIGN-SYSTEM.md`); never author a token in hex or rgb.

## REST / DRF

```ts
const BASE = import.meta.env.PUBLIC_API_URL;

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) throw new Error(String(res.status));
  return res.json() as Promise<T>;
}
```

Call from Astro frontmatter / server endpoints. Pass plain serializable props to Svelte. Secrets never in `PUBLIC_*`.

## Django HTMX

- Point `hx-*` at Django fragment URLs  
- CSRF / cookies as Django requires  
- Server returns HTML; Astro may only own the shell  

## Webhooks

```ts
import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request }) => {
  const raw = await request.text();
  if (!verify(raw, request.headers)) return new Response(null, { status: 401 });
  await forward(raw);
  return new Response(null, { status: 204 });
};
```

## Forbidden without explicit user justification

| Pattern | Why |
|---------|-----|
| React / Vue / Solid / Alpine | Outside the two options |
| Hand-rolled UI scripts | Use HTMX or Svelte |
| Other component kits | shadcn-svelte foundation only |
| Large HTML in `.astro` | Belongs in `.svelte` |
| `<title>` or other static text inline in `.astro` | Belongs in a zero-hydration `.svelte` piece |
| `client:*` on static trees | Zero-JS preference |
| Svelte 4 `export let` | Svelte 5 runes only |
| json-render / generative catalogs | Different product |
| `px` for spacing/sizing | rem is the standard unit |
| rgb/hsl on a token | OKLCH only, in `app.css` |
