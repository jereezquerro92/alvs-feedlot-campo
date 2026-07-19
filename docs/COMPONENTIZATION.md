---
title: COMPONENTIZATION
type: reference
status: active
created: 2026-07-15
tags: [frontend, componentization, design-system]
---

# COMPONENTIZATION

Content home for [[adr-04-frontend-and-design-system]] r9. Stack context: [[FRONTEND]]; component layering: [[DESIGN-SYSTEM]], [[MELT-UI]].

> [!important] This doc owns technique and folder paths — not names
> This document is the SSOT for the componentization **technique** (the `.astro`-routes-only / `.svelte`-everything-else rule) and the **folder-path taxonomy** (which category a component's file lives under). It is **not** where a component's canonical name is decided: **[[GLOSSARY]] is the naming authority for every component name**, per [[adr-01-glossary-and-localization]] rule 1 ([[adr-00-adr-doctrine]] owner ruling, issue #206). The Component index below records the name-to-folder mapping for reference, but a new component's name still gets its GLOSSARY row first, before its first use, exactly like any other identifier-worthy term.

## The rule

**`.astro` is for routes and layouts only.** A file under `src/pages/**.astro` or `src/layouts/**.astro` composes components and holds page-level wiring — data fetching, prop assembly, layout slots — and authors no non-trivial markup of its own. Every other visual unit is a `.svelte` component, including a page's title: `<title>{title}</title>` hand-authored inline in a `.astro` file is a defect under this rule, not a style preference.

- **A static title still ships zero client JS.** A `.svelte` component rendered inside Astro's SSR output with no hydration directive (`client:load`, `client:visible`, etc.) produces plain server-rendered markup — the componentization mandate costs nothing at runtime.
- **A `.svelte` file with no client directive is still rung 1 of the interactivity ladder** ([[FRONTEND]], [[adr-04-frontend-and-design-system]] r3) — this rule is about markup *ownership*, not about adding hydration. Escalating to an actual island remains a separate, per-feature decision.

## The component contract, and the harness that enforces it

[[adr-22-showcase-ready-components]] gives every component a contract: it renders with zero props without throwing (rule 1), and its default invocation performs no mutating action (rule 2). The point is reuse without a fork — the same vendored component serves the gallery and a real app page, so a gallery-only copy never has to exist.

**Rule 1 is enforced by test, not by review.** `frontend/tests/component-mount.test.ts` globs this folder tree, mounts every component with zero props, and fails on a throw. The suite discovers its own subjects: a new `.svelte` file here is covered the moment it lands, with no list to update. That self-discovery is the mechanism — an enumerated list of subjects decays back into the code-review-only enforcement the harness replaces.

**Run it with `bun run test`, never bare `bun test`.** The suite needs two export conditions — `browser`, for Svelte's client runtime, and `svelte`, the only condition the `melt` package publishes — and they live on the `test` script in `frontend/package.json`. `bunfig.toml` has no equivalent setting, so a bare `bun test` resolves Svelte's *server* build and fails every mount. CI runs the script for this reason ([[FRONTEND]]).

Two more mechanics worth knowing before touching that file. It is the only DOM-bearing suite in the repo, so it registers happy-dom itself instead of through a `bunfig` preload — `bun test` runs every file in one process, and happy-dom's CORS-enforcing HTTP globals break the SSR server and stub backend `smoke.test.ts` stands up. And `bun test` never goes through Vite, so the file carries its own Svelte loader; without it an imported `.svelte` resolves to a path string.

**The context-bound exemption.** A component whose only valid invocation is as a child of a parent compound component — reading a context that parent sets, never mounted bare by a caller — is exempt from rule 1, and the harness's `CONTEXT_BOUND` list is that exemption's exact membership. The vendored `ui/alert-dialog/` parts are today's only members: each throws on a bare mount by design, stating the parent requirement. The parent is bound by rule 1 with no exemption, and the list holds exact paths — never a directory wildcard — so a new component can never drift into the exemption unnoticed.

**Rule 2 is covered in part by test, in part by review — and the same file says which is which.** `frontend/tests/component-mount.test.ts` now also mounts every discovered component with zero props, stubs `fetch` to record any non-GET method, flushes pending effects, and fails if a mutating request (POST/PATCH/DELETE) went out. That catches the mount-and-effect vector: a mutation wired into `onMount` or an `$effect`, which fires with no caller wiring. What it does **not** cover is the click/interaction-fired mutation — a Save or logout that only PATCHes or POSTs from a handler, its action prop caller-wireable (today `ProfileForm` and `ThemeCard`'s `PATCH /api/me/`, `SessionBadge`'s logout POST). Dispatching clicks to reach that path would demand routing each action through a no-op-defaulting prop — a component change outside this test's scope — so it stays a code-review gate. This is a real control over one vector plus an explicit limit on the other, not a claim of full coverage; [[adr-22-showcase-ready-components]] states the limit rather than implying a control that does not exist.

## Folder tree

```
src/lib/components/
  primitives/        # PageTitle.svelte, SectionTitle.svelte — .svelte, zero-hydration
  ui/                # shadcn-svelte vendored set (adr-04 r4), incl. table/
  data/              # DataTable, NumericValue, StatusBadge, ChipFilterBar, Pagination, Collapsible, Tree
  dashboard/         # MetricTile, MetricTileStrip, EntityCard, EntityGrid, SummaryCard
  chat/              # ChatUI, ChatMessageList, ChatComposer — the router's chat surface (CHATBOT)
  auth/              # AuthPanel, SessionBadge, ProfileForm
  form/              # Select, Combobox, Checkbox, Switch, DatePicker, DateRangePicker, PinInput, TagsInput — Melt builders (adr-04 r8 default)
  nav/               # Tabs, DropdownMenu, ContextMenu, Menubar, TableOfContents — Melt builder(s) + hand-rolled fallbacks
  feedback/          # Toast — Melt builder, module-level `toaster` singleton
  overlay/           # Dialog, Drawer, Accordion, ConfirmDialog, Tooltip, Popover, HoverCard, ScrollArea, SidePanel — Melt builders (adr-04 r8 default), SOLID open/close primitives
  theme/             # ThemeModeToggle, QuickThemeToggle, ThemeCard — Melt-builder theme controls
  showcase/          # AlertDialogDemo, TabsDemo, DropdownMenuDemo, ContextMenuDemo, MenubarDemo, TableOfContentsDemo, TooltipDemo, PopoverDemo, HoverCardDemo, CollapsibleDemo, TreeDemo, ScrollAreaDemo, SidePanelDemo, ToastTriggerDemo — gallery-only demo compositions, not app surface
  views/             # LobbyView, ProfileView, ShowcaseView, ShowcaseGalleryView, ChatView — one zero-hydration page body per route
```

**Every component name here is business-agnostic** — no domain (financial, HR, inventory, ...) is ever spelled into a folder or component name. A component's fitness for a specific kind of dashboard or report is recorded as guidance in the Component index below, never encoded in its identifier: a project cloning this template reads `DataTable`, not `FinancialTable`, and decides for itself where it fits.

Each category resolves its own components through the layering order owned by [[DESIGN-SYSTEM]] and [[MELT-UI]]: Melt builder first, vendored shadcn-svelte second, hand-rolled custom third ([[adr-04-frontend-and-design-system]] r8). `overlay/` is the layer most likely to need a Melt builder from scratch, since no shadcn-svelte equivalent for a generic (non-alert) dialog, a drawer, or an accordion is vendored in `ui/` today.

## Component index

Names here are reference copies of what [[GLOSSARY]] already decided, not the point of first decision — see the callout above.

| Component | Folder | Purpose | Recommended for |
|---|---|---|---|
| `PageTitle` | `primitives/` | Page-level heading, zero-hydration | Every page |
| `SectionTitle` | `primitives/` | Section-level heading, zero-hydration | Every page |
| `CornerNavTriangle` | `primitives/` | Fixed bottom-right isosceles-triangle nav, hand-rolled SVG (rounded on all corners incl. the screen-corner vertex — no Melt builder for this shape), cycles home→chat→showcase | Site-wide 3-front navigation |
| `DataTable` | `data/` | Generic sortable/expandable data table | Financial dashboards & reporting (line-item tables, statements) |
| `NumericValue` | `data/` | Formatted numeric/currency display, sign-aware coloring | Financial dashboards & reporting (amounts, balances) |
| `StatusBadge` | `data/` | Enum-to-label/variant badge | Financial dashboards & reporting (state indicators); general enum display |
| `ChipFilterBar` | `data/` | Horizontally-scrollable, countable filter chips | Financial dashboards & reporting (state/category filters) |
| `Pagination` | `data/` | Prev/next + numbered page controls, hand-rolled (no Melt Pagination builder) | Pairs with `DataTable` for paged result sets |
| `Collapsible` | `data/` | Single expand/collapse disclosure, Melt Collapsible builder | Generalizes the per-row expand `DataTable` already does |
| `Tree` | `data/` | Hierarchical expandable/selectable tree, Melt Tree builder, self-recursive via `<svelte:self>` | Holding/intercompany account hierarchies |
| `MetricTile` | `dashboard/` | Single clickable KPI tile | Financial dashboards & reporting (KPI strips) |
| `MetricTileStrip` | `dashboard/` | Row of `MetricTile`, active-filter aware | Financial dashboards & reporting |
| `EntityCard` | `dashboard/` | Card summarizing one entity's key stats | Financial dashboards & reporting (account/holding cards); general entity display |
| `EntityGrid` | `dashboard/` | Grid of `EntityCard` | Financial dashboards & reporting; general entity display |
| `SummaryCard` | `dashboard/` | Pinned aggregate/rollup card | Financial dashboards & reporting |
| `ChatUI` | `chat/` | Composed chat surface (list + composer) | [[CHATBOT]] router UI |
| `ChatMessageList` | `chat/` | Renders structured router outcomes only, never free prose | [[CHATBOT]] router UI |
| `ChatComposer` | `chat/` | Posts raw user text to the router endpoint | [[CHATBOT]] router UI |
| `AuthPanel` | `auth/` | Session-aware auth actions | Any authenticated page |
| `SessionBadge` | `auth/` | Compact current-session indicator | Any authenticated page |
| `ProfileForm` | `auth/` | Editable profile fields (nickname, avatar visibility) with confirm-guarded save | `/profile/` |
| `Select` | `form/` | Single-select popover, Melt builder | Forms needing a closed-option field |
| `Combobox` | `form/` | Searchable single-select, Melt builder | Forms needing a filterable option field |
| `Checkbox` | `form/` | Boolean checkbox, Melt Toggle builder | Forms needing a boolean field |
| `Switch` | `form/` | Boolean pill/thumb switch, Melt Toggle builder | Forms needing a boolean field styled as a switch |
| `DatePicker` | `form/` | Single-date filter, Melt Popover over a native `<input type="date">` | Financial dashboards & reporting (due dates, cutoffs) |
| `DateRangePicker` | `form/` | From/to date-range filter, Melt Popover over two native `<input type="date">` | Financial dashboards & reporting (statement periods) |
| `PinInput` | `form/` | Numeric confirmation-code field, Melt PinInput builder | Second-factor confirm gates |
| `TagsInput` | `form/` | Chip add/remove field, hand-rolled (no Melt TagsInput builder) | Multi-filter or recipients entry |
| `Calendar` | `form/` | Inline single-month grid for single-date selection, hand-rolled (no Melt Calendar builder) | Inline date filters where a popover is unwanted |
| `RangeCalendar` | `form/` | Inline single-month grid for from/to range selection, hand-rolled (no Melt RangeCalendar builder) | Inline date-range filters where a popover is unwanted |
| `Slider` | `form/` | Numeric range control, Melt Slider builder | Threshold/utilization filters |
| `ToggleGroup` | `form/` | Single-select segmented option group, composed of Melt Toggle builder instances (no dedicated Melt ToggleGroup builder) | View-mode switches, small filter chip sets |
| `Tabs` | `nav/` | Tabbed navigation, Melt builder | Any feature needing tabbed content |
| `DropdownMenu` | `nav/` | Floating action menu, Melt Popover + hand-rolled roving-focus/typeahead menu semantics (no Melt Dropdown Menu builder in 0.44) | Row actions, user menus |
| `ContextMenu` | `nav/` | Right-click-triggered menu at the pointer, Melt Popover + the same hand-rolled roving-focus/typeahead semantics as `DropdownMenu` (no Melt Context Menu builder in 0.44) | Row/canvas right-click actions |
| `Menubar` | `nav/` | Horizontal row of `DropdownMenu`-style Melt Popover menus with cross-trigger roving focus, hand-rolled composition (no Melt Menubar builder in 0.44) | App-shell top menu bars |
| `TableOfContents` | `nav/` | Plain anchor-link nav to in-page headings with `IntersectionObserver` active-section highlighting, hand-rolled (no Melt Table of Contents builder) | Long-form doc/report pages |
| `Toast` | `feedback/` | Toast notifications, Melt Toaster builder; `toaster` is a module-level singleton | Any feature needing transient confirmation/error feedback |
| `Dialog` | `overlay/` | Generic (non-alert) modal | Any feature needing a modal |
| `Drawer` | `overlay/` | Side-panel slide-in | Any feature needing a side panel |
| `Accordion` | `overlay/` | Collapsible section | Any feature needing progressive disclosure |
| `ConfirmDialog` | `overlay/` | Confirm-labeled alert-dialog wrapper | Destructive/confirm-gated actions |
| `Tooltip` | `overlay/` | Hover/focus hint, Melt builder | Any feature needing a short contextual hint |
| `Popover` | `overlay/` | Click-triggered floating content, bare Melt Popover builder (no menu semantics) | Quote boxes, contextual filters, any content richer than a Tooltip hint |
| `HoverCard` | `overlay/` | Hover/focus-triggered rich preview, Melt Popover + hand-rolled hover semantics (no dedicated Melt Hover Card builder in 0.44) | Link/username previews |
| `ScrollArea` | `overlay/` | Constrained-height scroll container, hand-rolled (no Melt ScrollArea builder in 0.44) with a themed scrollbar | Drawer/chat long content that must not grow the page |
| `SidePanel` | `overlay/` | Persistent, viewport-docked collapsible panel (`side` left/right) with a peek tab, hand-rolled — slides its full width off-screen, animated via CSS transform; distinct from `Drawer` (modal slide-in) | App-shell navigation rails & context/detail panels |
| `ThemeModeToggle` | `theme/` | Light/Dark switch, Melt builder | Any page exposing a mode toggle |
| `QuickThemeToggle` | `theme/` | Cookie-only mode toggle, decoupled from `/profile` | `SessionBadge`'s ☰ menu (both branches) |
| `ThemeCard` | `theme/` | Full theme editor (mode, bgPreset, colors, radius) persisted via `PATCH /api/me/` | `/profile/` |
| `AlertDialogDemo` | `showcase/` | Standalone composition of the raw `ui/alert-dialog` primitives | `/showcase/components/` gallery only |
| `TabsDemo` | `showcase/` | Composition of `nav/Tabs` supplying its parameterized `content` snippet | `/showcase/components/` gallery only |
| `DropdownMenuDemo` | `showcase/` | Composition of `nav/DropdownMenu` supplying realistic row-action sample data | `/showcase/components/` gallery only |
| `ContextMenuDemo` | `showcase/` | Composition of `nav/ContextMenu` supplying a labeled right-click region and realistic sample data | `/showcase/components/` gallery only |
| `MenubarDemo` | `showcase/` | Composition of `nav/Menubar` supplying a realistic File/Edit sample menu set | `/showcase/components/` gallery only |
| `TableOfContentsDemo` | `showcase/` | Composition of `nav/TableOfContents` supplying sample section links | `/showcase/components/` gallery only |
| `TooltipDemo` | `showcase/` | Composition of `overlay/Tooltip` supplying its parameterized `trigger` snippet | `/showcase/components/` gallery only |
| `PopoverDemo` | `showcase/` | Composition of `overlay/Popover` supplying its parameterized `content` snippet | `/showcase/components/` gallery only |
| `HoverCardDemo` | `showcase/` | Composition of `overlay/HoverCard` supplying its parameterized `preview` snippet | `/showcase/components/` gallery only |
| `CollapsibleDemo` | `showcase/` | Composition of `data/Collapsible` supplying its parameterized `content` snippet | `/showcase/components/` gallery only |
| `TreeDemo` | `showcase/` | Composition of `data/Tree` with no props — its default sample hierarchy is already realistic | `/showcase/components/` gallery only |
| `ScrollAreaDemo` | `showcase/` | Composition of `overlay/ScrollArea` supplying its parameterized `content` snippet | `/showcase/components/` gallery only |
| `SidePanelDemo` | `showcase/` | Composition of `overlay/SidePanel` mounting one left and one right instance (both collapsed by default) with an inline note | `/showcase/components/` gallery only |
| `ToastTriggerDemo` | `showcase/` | Button that pushes a sample toast onto the shared `toaster` singleton | `/showcase/components/` gallery only |
| `CornerNavTriangleDemo` | `showcase/` | Composition of `primitives/CornerNavTriangle`, docked inside a clipped gallery box (zero props, safe default per adr-22) | `/showcase/components/` gallery only |
| `LobbyView` | `views/` | The `/` page body — header, lobby cards, denied/pending states; islands via named slots | `index.astro` only |
| `ProfileView` | `views/` | The `/profile/` page body; form + theme islands via default slot | `profile.astro` only |
| `ShowcaseView` | `views/` | The `/showcase/` page body; auth island via default slot | `showcase.astro` only |
| `ShowcaseGalleryView` | `views/` | The `/showcase/components/` gallery body; twenty islands via named slots | `showcase/components.astro` only |
| `ChatView` | `views/` | The `/chatui/` canvas wrapper; chat island via default slot | `chatui.astro` only |

**The `views/` category is the page-body half of the rule above:** every route's markup body lives here as a **zero-hydration** `.svelte` component (no `client:*` directive — rung 1), and the owning `.astro` page composes exactly one view plus its slotted islands. Interactive controls stay declared in the `.astro` file with their `client:*` directive and enter the view through named slots — hydrating a whole view to embed one island is the over-hydration this split exists to prevent.

## Why a folder per category, not a flat `components/`

A flat directory hides which components are reusable-general (`ui/`, `overlay/`, `primitives/`) versus which are business-agnostic-but-purpose-shaped (`data/`, `dashboard/`, `chat/`, `auth/`). Splitting by category keeps a future template consumer able to reason about a whole category at once, without any category name locking the components inside it to one domain.
