# shadcn-svelte (second-choice foundation, design-system agnostic)

Official: https://www.shadcn-svelte.com/docs  
Astro install: https://www.shadcn-svelte.com/docs/installation/astro  
CLI: `shadcn-svelte@1.4.1+` (always `@latest` when scaffolding)

## What it is

- **Code distribution system** + accessible primitives (Bits UI, Tailwind).  
- Components are **copied into the project** and owned by the repo.  
- **Not a closed design brand.** Tokens, colors, radius, fonts = project design system.  
- **Second choice, not optional** in kdx-astro-7 — Melt UI builders come first (`references/melt-ui.md`); reach here for a standard, pre-built shape a builder would just reinvent. Do not swap for Daisy/MUI/etc. without explicit user justification.

## Workflow for every UI piece

1. **Decide Melt vs shadcn first** — a builder (`melt/builders`) if the piece needs full custom control, this workflow if it doesn't (`references/melt-ui.md`)  
2. **MCP `shadcn-svelte`** — search/list component, read source/demo/deps  
3. **CLI** — `bunx shadcn-svelte@latest add <component>` if not in repo  
4. **Compose** — product components in `src/components/**` wrap `ui/*` primitives  
5. **Theme** — adjust CSS variables / Tailwind theme; do not fork primitives needlessly  

## Init (Astro)

```bash
bunx astro add svelte --yes
bunx astro add tailwind --yes
bunx shadcn-svelte@latest init
```

Creates `components.json`, paths, and base styles. Follow CLI prompts; prefer TypeScript + existing `src/lib` aliases.

## Add components

```bash
bunx shadcn-svelte@latest add button
bunx shadcn-svelte@latest add card dialog input label select table
```

Multiple names per invoke. After add: import from the path in `components.json` (typical `$lib/components/ui/...`).

## Common primitives (install as needed)

Layout / structure: `card` `separator` `scroll-area` `resizable`  
Forms: `button` `input` `textarea` `label` `checkbox` `radio-group` `select` `switch` `slider` `form`  
Overlay: `dialog` `drawer` `sheet` `popover` `dropdown-menu` `tooltip` `alert-dialog`  
Nav: `tabs` `navigation-menu` `breadcrumb` `pagination` `menubar`  
Feedback: `alert` `badge` `progress` `skeleton` `sonner`  
Data: `table` `avatar` `calendar`  

Exact set: **ask the MCP** (source of truth for huntabyte registry).

## Composition rules

- Build features from primitives; avoid one-off CSS clones of Button/Input  
- Variants via component API (`variant`, `size`) before custom classes  
- Keep `ui/` as low-level; app shells live outside `ui/`  
- Interactive overlays often need a Svelte island (`client:visible`) when used with client state  

## MCP tools (intent)

Use server tools to:

- List available components  
- Fetch implementation / demo  
- Discover dependencies before `add`  

Never invent props that contradict MCP/CLI source.

## Forbidden without explicit user justification

- Installing React shadcn/ui into an Astro+Svelte app  
- Second component library alongside shadcn-svelte  
- Hand-rolling accordion/dialog when the primitive exists  
- Depending on `@json-render/shadcn-svelte` unless user asked for json-render  
