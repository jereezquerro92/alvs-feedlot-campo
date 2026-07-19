---
title: MELT-UI
type: reference
status: active
created: 2026-07-14
tags: [frontend, melt, design-system]
---

# MELT-UI

Melt is the headless builder layer beneath the frontend's component stack. Stack context: [[FRONTEND]]; visual/component ownership: [[DESIGN-SYSTEM]]; rule: [[adr-04-frontend-and-design-system]]; version pin: [[REQUIREMENTS]].

## The layering — upstream lineage, not all installed here

```
Melt (headless builders)  →  Bits UI (v2, built on melt)  →  shadcn-svelte (styled, vendored)
```

This diagram is **upstream lineage**: shadcn-svelte's components are historically and architecturally derived from Bits UI, which is itself built on Melt. It is not a description of three active dependencies of this repo. Only two of the three are actually installed here — `melt` (pinned in [[REQUIREMENTS]]) and the vendored shadcn-svelte components under `frontend/src/lib/components/ui/`, which hand-roll their own state via `getContext`/`setContext` rather than consuming Bits UI primitives. **Bits UI has no row in [[REQUIREMENTS]] and is not a dependency of this repo**; adopting it would need that row first ([[adr-02-initial-stack]] r1).

- **Melt** — `melt` npm package, Svelte-5 runes-native. Highest control, lowest-level primitive: no markup, no styling, just behavior (state, ARIA, keyboard handling) exposed as reactive objects you wire into your own elements.
- **Bits UI v2** — upstream lineage only, the headless component library shadcn-svelte's own components are built on. Not installed in this repo.
- **shadcn-svelte** — the styled, vendored default ([[adr-04-frontend-and-design-system]] r4). Most work stays here.

Melt is not a replacement for shadcn-svelte — it is what you reach for when shadcn-svelte's shipped markup/behavior is not enough and you need to build a fully custom component from the primitive layer up.

## How to create a Melt component

1. **Install**: `bun add melt` ([[FRONTEND]] — bun is the only package manager; npm is prohibited).
2. **Choose a method** — Melt ships two:
   - **Builders** — `import { Toggle } from "melt/builders"`; instantiate a class, spread its attribute objects onto your own markup. Full control over the DOM structure.
   - **Components** — `import { Toggle } from "melt/components"`; a render-prop snippet component. Less markup control, faster to wire.
3. **Builder pattern** (the sanctioned default for custom components) — this is the real, vendored example, trimmed from `frontend/src/lib/components/ThemeModeToggle.svelte`:

```svelte
<script lang="ts">
  import { Toggle } from "melt/builders";
  import type { ThemeMode } from "$lib/theme";

  let { mode = $bindable<ThemeMode>("light"), disabled = false }:
    { mode?: ThemeMode; disabled?: boolean } = $props();

  const toggle = new Toggle({
    value: () => mode === "dark",
    onValueChange: (isDark) => { mode = isDark ? "dark" : "light"; },
    disabled: () => disabled,
  });
</script>

<button type="button" {...toggle.trigger}>
  {toggle.value ? "Dark" : "Light"}
</button>
```

(Styling and the mode icon are elided here for brevity; the shipped file is the full source.)

Key mechanics:

- **Reactive props are passed as getters** — `disabled: () => disabled`, `value: () => mode === "dark"` — never as a plain value, so the builder tracks the caller's state reactively.
- **Attribute objects are spread onto elements** — `{...toggle.trigger}` — Melt computes the ARIA attributes, event handlers, and IDs; the caller owns the tag and any classes/styling on top.
- Builder state (`toggle.value`, etc.) reads back reactively for rendering.

The **Components** method (`melt/components`) trades some of that markup control for a snippet-based render prop — reach for it when a builder's manual wiring is more ceremony than the component needs; otherwise builders are the default for a fully custom piece.

## Where this template uses it

Two real, vendored examples, both under `frontend/src/lib/components/`, both driving the token-based theme controls in [[DESIGN-SYSTEM]]'s user-configurable subset — neither has a shadcn-svelte equivalent that ships the needed behavior (Bits UI, upstream lineage only, is not installed in this repo and so is not a live alternative to weigh — see "The layering" above):

1. **`ThemeModeToggle.svelte`** — the `Toggle` builder shown above, a fully custom light/dark control.
2. **`ThemeCard.svelte`'s background-preset selector** — a second builder, `RadioGroup` from `melt/builders`, driving the `bgPreset` choice (`default` | `melt`, [[DESIGN-SYSTEM]]):

```svelte
<script lang="ts">
  import { RadioGroup } from "melt/builders";

  const bgGroup = new RadioGroup({
    value: () => bgPreset,
    onValueChange: (value) => { bgPreset = value as ThemeBgPreset; },
    orientation: () => "horizontal",
  });
</script>

<Label {...bgGroup.label}>Background preset</Label>
<div {...bgGroup.root} class="inline-flex gap-2">
  {#each BG_PRESETS as preset (preset)}
    {@const item = bgGroup.getItem(preset)}
    <button type="button" {...item.attrs}>{preset}</button>
  {/each}
</div>
```

Same pattern as `Toggle`: reactive getters in, attribute objects out (`bgGroup.root`, `bgGroup.label`, `item.attrs`) spread onto plain markup. `RadioGroup` additionally exposes one `getItem(value)` per option, each carrying its own `checked` state for conditional styling. Full file: `frontend/src/lib/components/ThemeCard.svelte`.

## Melt vs shadcn-svelte — the choice criteria

This doc is the content home for this list; [[adr-04-frontend-and-design-system]] links here rather than restating it.

**Use Melt UI when:**
- full control over markup & behavior
- a highly custom design (not shadcn defaults)
- minimalism & extreme performance
- comfortable with a lower-level "primitive" approach (like Radix UI, more flexible)
- building your own design system long-term

**Use shadcn-svelte (or a combination) when:**
- you want to move fast at the start
- you like shadcn's visual style and want to tweak it
- you're fine using pre-built components

Default posture in this template: Melt-first ([[adr-04-frontend-and-design-system]] r8, [[DESIGN-SYSTEM]]'s component layering). A new component reaches for a Melt builder before considering a vendored shadcn-svelte default; shadcn-svelte is the second choice, reached for when a Melt builder doesn't already cover the needed shape, and a fully custom component is the last resort — decided per-feature, same spirit as the [[HTMX]] ladder decision in [[BDD]].
