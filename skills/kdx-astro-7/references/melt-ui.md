# Melt UI (component layer, first choice)

Doctrine mirrors `~/Templates/astro-drf-aws/docs/MELT-UI.md`. Official: https://next.melt-ui.com/ · pkg `melt` (Svelte-5 runes-native).

## What it is

- **Headless builder layer.** No shipped markup, no CSS — just behavior (state, ARIA, keyboard handling) exposed as reactive objects you wire onto your own elements.
- **The lineage** (upstream context only, not three active deps): `Melt (builders) → Bits UI (upstream lineage, not installed) → shadcn-svelte (styled, vendored)`. Only `melt` and vendored shadcn-svelte are actually installed in this template.
- Not a replacement for shadcn-svelte — it is the layer you reach for **first**, before shadcn, whenever a piece needs full control over markup and behavior.

## Builder-first workflow

1. **Default assumption: reach for a Melt builder.** Any new UI piece starts here, not at shadcn.
2. **Pick a method** — Melt ships two:
   - **Builders** (`melt/builders`) — instantiate a class, spread its attribute objects onto your own markup. Full control over the DOM. This is the sanctioned default.
   - **Components** (`melt/components`) — a render-prop snippet component. Less markup control, faster to wire; use only when a builder's manual wiring is more ceremony than the piece needs.
3. **Fall to shadcn-svelte** (`references/shadcn-svelte.md`) only when the need is a standard, pre-built shape a builder would just reinvent — moving fast, liking shadcn's shipped visual style, a form input that needs no custom behavior.
4. **Hand-rolled markup outside both** is the last resort, same justification bar as any other forbidden pattern (`references/patterns.md` Forbidden table).

## How to implement a Melt builder as your own component

```svelte
<script lang="ts">
  import { Toggle } from 'melt/builders';
  import type { ThemeMode } from '$lib/theme';

  let { mode = $bindable<ThemeMode>('light'), disabled = false }:
    { mode?: ThemeMode; disabled?: boolean } = $props();

  const toggle = new Toggle({
    value: () => mode === 'dark',
    onValueChange: (isDark) => { mode = isDark ? 'dark' : 'light'; },
    disabled: () => disabled,
  });
</script>

<button type="button" {...toggle.trigger}>
  {toggle.value ? 'Dark' : 'Light'}
</button>
```

Key mechanics:

- **Reactive props are getters** — `disabled: () => disabled`, `value: () => mode === 'dark'` — never a plain value, so the builder tracks the caller's state reactively.
- **Attribute objects spread onto elements** — `{...toggle.trigger}` — Melt computes ARIA attributes, event handlers, IDs; the caller owns the tag and any classes/styling on top.
- Builder state (`toggle.value`, etc.) reads back reactively for rendering.
- A second builder, `RadioGroup`, follows the same shape (`root`/`label`/`getItem(value).attrs`) — see the template's `ThemeCard.svelte` for a live example driving a multi-option choice.

## When to choose Melt vs vendoring shadcn

**Melt (first choice) when:**
- full control over markup & behavior is needed
- the design is genuinely custom, not a shadcn default
- minimalism / extreme performance matters
- comfortable with a lower-level primitive approach (Radix-like flexibility)
- building toward a long-term, project-owned design system

**shadcn-svelte (second choice) when:**
- moving fast on a standard shape matters more than full control
- shadcn's shipped visual style already fits, only needs token-level tweaking
- a pre-built primitive covers the behavior with no bespoke wiring

Install: `bun add melt` (bun only — `references/stack.md`). Never install `@melt-ui/svelte` (legacy pre-runes package).
