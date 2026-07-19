# Svelte 5 in Astro 7

Docs: https://svelte.dev/docs/svelte · https://docs.astro.build/en/guides/integrations-guide/svelte/

## Integration

- Package: `@astrojs/svelte@9` + `svelte@^5`  
- Preprocess: `vitePreprocess()` in `svelte.config.js`  
- Import `.svelte` from thin `.astro` pages/layouts  

## Hydration

| Directive | When |
|-----------|------|
| (none) | **Default** — SSR HTML, no client runtime |
| `client:visible` | Preferred island |
| `client:idle` | Secondary |
| `client:load` | Rare — needed immediately |
| `client:only="svelte"` | SSR impossible only |

Never hydrate “because the file is Svelte”.

## Runes (only syntax)

```svelte
<script lang="ts">
  let { title = '', count = 0 }: { title?: string; count?: number } = $props();
  let n = $state(count);
  let double = $derived(n * 2);

  $effect(() => {
    if (n > 99) n = 99;
  });
</script>

<button type="button" onclick={() => (n += 1)}>{title}: {double}</button>
```

| Rune | Role |
|------|------|
| `$props()` | Inputs (typed) |
| `$state` | Mutable local state |
| `$derived` | Computed |
| `$effect` | Side effects (sparingly) |
| `$bindable` | Two-way prop when required |

**Do not use:** `export let`, stores-as-default-state, Svelte 4 slot APIs where snippets replace them.

## Snippets / children

```svelte
<script lang="ts">
  import type { Snippet } from 'svelte';
  let { children }: { children: Snippet } = $props();
</script>

<div class="wrap">{@render children()}</div>
```

From Astro, pass children into Svelte; Svelte uses `<slot />` or snippets per current Svelte 5 docs.

## Events

Use DOM `onclick` / `oninput` (Svelte 5) rather than `on:click` legacy where the project is pure Svelte 5.

## Component rules

- One concern per file; extract named pieces early  
- English identifiers; prefer no comments (never non-English)
- Props serializable when the component is hydrated  
- Prefer SSR; escalate to `client:*` only after HTMX is insufficient  

## Anti-patterns

- Mixing frameworks inside one `.svelte` file  
- Importing `.astro` into `.svelte`  
- Shipping stores for server data already available as props  
- Giant god-components instead of composition  
