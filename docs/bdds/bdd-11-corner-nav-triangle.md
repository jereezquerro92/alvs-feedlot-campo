---
title: bdd-11-corner-nav-triangle
type: bdd
status: building
created: 2026-07-18
tags: [bdd, frontend, nav, custom]
---

# bdd-11 — corner nav triangle (home / chat / showcase cycling)

## Use case

As **any visitor**, when I look at the **bottom-right corner of the
viewport**, I see a fixed, isosceles-triangle button filling that corner,
showing an icon for one of the three fronts of the system (home / chat /
showcase); when I **click it**, I am **navigated to that front**, and the
icon **advances to the next front in the cycle** so the next click takes me
further around the loop, never back to the one I just left (issue #374).

## Chosen cycle semantics (locked)

Three fronts, one fixed order: `home -> chat -> showcase -> home -> ...`.
The icon shown is always **the destination of the next click** — not the
current page. On `/` it shows the chat icon (next stop); on `/chatui/` it
shows the showcase icon; on `/showcase/components/` it shows the home icon.
This reads more naturally than a click-then-advance counter decoupled from
the URL: the icon is *derived from the current route*, not from
client-only state, so a full page reload (real navigation, not an SPA
transition — this is rung-1 plain anchors, no client router) always shows
the objectively correct next destination with no stale-state risk. The
issue's proposed alternative ("cycle state advances on click, independent
of route") is rejected in favor of this route-derived reading, which is
simpler and needs no persisted client state at all.

## Scenarios

```gherkin
Scenario: on the home page, the triangle offers "next: chat"
  Given a visitor is on "/"
  When the page renders
  Then the corner triangle shows the chat icon

Scenario: on the chat page, the triangle offers "next: showcase"
  Given a visitor is on "/chatui/"
  When the page renders
  Then the corner triangle shows the showcase icon

Scenario: on the showcase page, the triangle offers "next: home"
  Given a visitor is on "/showcase/components/"
  When the page renders
  Then the corner triangle shows the home icon

Scenario: clicking navigates via a plain anchor
  Given the corner triangle is rendered on any of the three fronts
  When the visitor clicks it
  Then the browser navigates (rung-1 plain `<a href>`, full page load,
    no client-side router) to the next front in the fixed cycle

Scenario: default invocation with zero props is safe
  Given the component is mounted with no props supplied (e.g. in the
    showcase gallery)
  Then it renders its default state (home front target) without throwing
    (adr-22 r1) and performs no navigation or mutating action on mount
    (adr-22 r2) — the gallery composition supplies no real route target
```

## Frontend half

New component `CornerNavTriangle.svelte` under
`frontend/src/lib/components/primitives/` (peer of `HomeTriangle.svelte`,
a distinct component — not a fork or replacement of #255's `HomeTriangle`,
which stays top-left, right-angle, single-target, unmodified).

- **Shape**: isosceles triangle filling the bottom-right viewport corner,
  `position: fixed; bottom: 0; right: 0`. Built with a CSS `clip-path`
  polygon (same technique `HomeTriangle` already uses for its right-angle
  cut), but **all three corners share one identical corner-radius**,
  including the vertex touching the screen's physical corner — a plain
  3-point `clip-path` polygon cannot round any vertex, so this is
  necessarily a **hand-rolled custom component**: no Melt builder exists
  for a rounded-corner arbitrary polygon (ladder rung 3, last resort,
  [[adr-04-frontend-and-design-system]] r8, [[MELT-UI]]) — the ladder is
  honored by explicitly ruling out Melt/shadcn first, not skipped.
  Mechanism: an SVG `<path>` (not a CSS `clip-path`) with rounded corners
  via cubic-bezier corner-arcs at a fixed radius, filled with
  `fill="var(--primary)"` referenced from the token layer — the one place
  a token is read from raw SVG `fill` rather than a Tailwind utility class,
  since `clip-path`/CSS corner-rounding on an arbitrary triangle is not
  expressible in Tailwind utilities alone.
- **Fill**: `--primary` token (orange), light/dark via the existing
  `.dark` pair — no new token needed ([[DESIGN-SYSTEM]]).
- **Icon**: a single inline SVG `currentColor` glyph, swapped per the
  `next` front (`home` | `chat` | `showcase`), colored via a new
  high-contrast token so it reads black-on-orange in both themes (see
  Design-system note below).
- **Sizes/offsets/radii**: `rem` only, no `px`, per [[DESIGN-SYSTEM]]
  "rem over px, everywhere".
- **Interaction**: rendered as a plain `<a href>` (rung 1, no client
  router) with `user-select: none` and `cursor: pointer` on the shape;
  `aria-label` states the destination front, localized via `t()`.
- **Zero-props default** (adr-22 r1/r2): with no `route` prop supplied,
  the component defaults to treating the current front as `home` (so it
  shows "next: chat") and its `href` resolves to a safe, real link
  (`/chatui/`) — a link is not a mutating action, so this satisfies rule 2
  with no caller wiring required, matching `HomeTriangle`'s precedent of
  defaulting to a real, inert-safe `href`.
- Added to `frontend/tests/component-mount.test.ts` coverage automatically
  (self-discovering glob, no list to update).
- Showcase gallery: a new `showcase/CornerNavTriangleDemo.svelte`
  composition (a wrapped/scaled box, same technique
  `HomeTriangleDemo.svelte` already uses to keep the fixed-position shape
  visible inside a gallery card instead of docking to the real page
  corner), wired into `ShowcaseGalleryView.svelte` + `components.astro`
  next to `HomeTriangleDemo`.
- `docs/COMPONENTIZATION.md` Component index gains `CornerNavTriangle` /
  `CornerNavTriangleDemo` rows in the same PR.
- **Global mount (#377):** `Base.astro` composes `CornerNavTriangle`
  once, after `<slot />`, passing `Astro.url.pathname` — every route
  that renders through `Base.astro` gets the real, permanent instance,
  zero-hydration (a plain `<a href>` needs no `client:*` directive).
  The showcase gallery's `CornerNavTriangleDemo` still exists on the
  page it lives on, confined inside its card via `[&_a]:!absolute`
  (stripping `position: fixed`) — the real global instance and the
  confined demo instance coexist without a visible double-triangle in
  the actual viewport corner.

### Design-system note (new token: `--corner-nav-icon`)

The icon needs a color that reads as high-contrast BLACK on the
`--primary` orange fill in BOTH themes. `--primary-foreground` cannot
serve this: it is tuned near-WHITE in light mode (`HomeTriangle`'s own
icon color, the opposite contrast direction this issue's "en NEGRO"
requirement needs) — reusing it would paint a near-invisible icon in
light mode. This entry therefore adds a new token, `--corner-nav-icon`
(`app.css`), with an explicit light AND dark pair per
[[DESIGN-SYSTEM]]'s "a color token without its `.dark` pair is a defect"
rule — both values fixed at the same near-black OKLCH tuning, since the
orange fill is what changes per mode, not the icon. This still honors
"tokens, not literals": the black requirement is met by a token
declared once in `app.css`, never a literal hex/OKLCH value written
into the component.

## Backend half

None. Pure frontend/routing feature — no new `[[API]]` row, no Django
change. The [[adr-07-development-flow]] checkpoint resolves immediately:
existing routes (`/`, `/chatui/`, `/showcase/components/`) already exist.

## Error handling

No network calls. The only degenerate case is being on a fourth,
unrecognized route (e.g. `/profile/`) — the component's route-to-next
resolver defaults to treating any unmatched route as `home` (same fallback
as the zero-props default), so the triangle never disappears or targets an
invalid href.

## Shadow-test spec

- `frontend/tests/component-mount.test.ts` — zero-props mount, no throw,
  no mutating fetch (adr-22 r1/r2), covered by the suite's existing glob
  (no manual list entry needed).
- `/showcase/components/` response body contains the CornerNavTriangle
  demo's marker (`frontend/tests/smoke.test.ts`, same pattern as
  `HomeTriangleDemo`'s existing check).
- Real-browser flow, `kodex`-only, via `chrome-devtools` MCP
  ([[AGENTS]]): visit `/`, confirm triangle shows chat icon
  bottom-right, rounded on all three corners including the screen-corner
  vertex; click it, confirm navigation to `/chatui/` and the icon now
  reads showcase; click again, confirm arrival at
  `/showcase/components/` with the icon reading home; click once more,
  confirm return to `/`. Verify in both light and dark mode: orange fill,
  high-contrast icon, no literal color anywhere.
- Until a project's shadow-test runner exists, this entry may reach
  `building`, never `shipped` ([[bdd-09-dropdown-menu-showcase]] caveat).
