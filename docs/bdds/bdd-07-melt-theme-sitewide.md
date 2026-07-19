---
title: bdd-07-melt-theme-sitewide
type: bdd
status: draft
created: 2026-07-14
tags: [bdd, theming, design-system, melt]
---

# bdd-07 — melt theme, sitewide default

## Use case

As **any visitor or signed-in user**, on **every route** in this app — home,
showcase, the component gallery, chat UI, profile, and the login/logout
affordances — the page renders melt-ui.com's actual dotted-background
construction (a neutral field, an amber dot-grid layer, and a top-fade
highlight above it, on a 1.5rem grid) as the **default** appearance, in
**dark mode by default**, matching melt-ui.com's own
`localStorage.getItem("mode") || "dark"` behavior. This is the DEFAULT for a
visitor with no saved preference — a signed-in user who has customized their
theme on `/profile` ([[bdd-06-profile-theming]]) still sees their own saved
`theme_config`, unchanged by this entry. No-flash SSR ([[DESIGN-SYSTEM]])
stays intact: the new defaults are picked up by `computeThemeSSRAttrs`
falling back to `DEFAULTS`, not by a `Base.astro` code change.

## Scenarios

### First visit, no cookie — sitewide dark+melt default

```gherkin
Given a visitor with no `theme` cookie set
When they request `/`, `/showcase/`, `/showcase/components/`, `/chatui/`,
  or `/profile` (while authenticated)
Then the server renders `<html class="dark" data-bg-preset="melt">` on
  every one of those routes — both defaults flipped from the prior
  `light`/`default` pair ([[DESIGN-SYSTEM]] "Theme application mechanism")
And no client-side repaint is needed — the correct theme is present in the
  first byte
```

### Distinct light and dark token pairs for the melt preset

```gherkin
Given the `melt` bgPreset is active (`[data-bg-preset="melt"]` on `<html>`)
When the page is NOT in dark mode
Then `--melt-dots-color` resolves to a full-opacity cream/tan dot
  (`oklch(0.90 0.05 75)`, melt-ui.com's `magnum-200` light value) against
  the neutral `--canvas` field
When `.dark` is ALSO present
Then `--melt-dots-color` resolves to a distinct, separately-declared muted
  burnt-amber value at reduced opacity (`oklch(0.48 0.13 45 / 0.25)`) — a
  real `.dark[data-bg-preset="melt"]` rule, not the light rule inherited
  unchanged by cascade. This names and fixes the prior defect: the old
  preset shipped one flat rule with no `.dark` pair at all
  ([[DESIGN-SYSTEM]]'s own "a token without its `.dark` pair is a defect"
  rule).
And in both modes a `--melt-fade-color` top-fade highlight
  (`linear-gradient(to bottom, var(--melt-fade-color) 0%, transparent 25%)`)
  layers above the dot grid, same near-white value in both modes — matching
  melt-ui.com's own dark-scoped `neutral-900` resolving to the identical
  literal as light's `neutral-100`
```

### QuickThemeToggle — cookie-only, session-local persistence

```gherkin
Given a visitor (signed in or not) who opens the ☰ menu in `SessionBadge`
  and finds the icon-only `QuickThemeToggle` control there
When they flip mode `light`/`dark`
Then `applyTheme` repaints `.dark` and the token overrides on
  `document.documentElement` immediately, client-side only
And `writeThemeCookie` mirrors the choice into the `theme` cookie
And NO `PATCH /api/me/` request is ever sent by this control — it is
  explicitly decoupled from `User.theme_config` and `/profile`'s
  `ThemeCard` ([[API]], [[bdd-06-profile-theming]])
And a signed-in user's `QuickThemeToggle` choice can therefore diverge from
  their saved `theme_config.mode` until they explicitly visit `/profile`
  and click Save there — a named trade-off, not a defect
```

### Component gallery — full coverage under the dark-melt default

```gherkin
Given a visitor at `/showcase/components/` with no `theme` cookie
Then the page renders in dark mode with the melt dotted background
And it exercises all 9 vendored `ui/` primitive groups — alert,
  alert-dialog, avatar, badge, button, card, input, label, separator
And it includes a live, standalone `ThemeModeToggle` demo (the vendored
  Melt-UI builder example, [[MELT-UI]]) distinct from the shadcn-svelte
  primitive sections above it
```

### Auth-surface inventory — no dedicated login/logout page

```gherkin
Given this repo has no dedicated login or logout page — `GET
  /accounts/login/` redirects straight to Cognito's hosted UI (external,
  unrestylable) and `POST /accounts/logout/` renders nothing of its own
When a visitor sees this app's own login/logout affordance
Then it is the `SessionBadge` (compact, home page) or `AuthPanel` (fuller,
  showcase page) Svelte island — both already 100% token-driven and expected
  to render correctly against the new dark-melt default with zero code
  changes
And in the rare case Cognito is unconfigured
  (`cognito_not_configured.html`, `COGNITO_*` unset and `AUTH_DEV_MODE`
  falsy), the fallback page renders a legible dark+amber-dot treatment using
  literal inline styles — it cannot import `frontend/src/styles/app.css`
  (a different Django service, no shared build pipeline) — an explicitly
  scoped, named exception to "everything is a CSS custom property"
  ([[DESIGN-SYSTEM]]), not an oversight
```

## Frontend half

No new backend surface. `frontend/src/lib/theme.ts`'s `DEFAULTS` constant is
the single seam: `mode: "dark"`, `bgPreset: "melt"` (was `"light"` /
`"default"`). `computeThemeSSRAttrs`/`applyTheme` already fall back to
`DEFAULTS` for any absent/malformed cookie or `theme_config` — no
`Base.astro` code change is needed to pick this up ([[DESIGN-SYSTEM]] "Theme
application mechanism"). The melt preset's CSS construction is retuned in
`frontend/src/styles/app.css` only — neutral `--canvas` field, dot-grid
layer, top-fade overlay, explicit `[data-bg-preset="melt"]` /
`.dark[data-bg-preset="melt"]` pair, 1.5rem grid — replacing the prior flat
amber-tint approach that had no `.dark` pair of its own.

`QuickThemeToggle.svelte` (housed in `SessionBadge`'s ☰ Melt Popover menu,
both the authenticated and the anonymous branch) wraps the existing
`ThemeModeToggle` Melt builder ([[MELT-UI]]); its cookie-only semantics are
the same pattern `ThemeCard`'s live-preview path already uses, minus the
`PATCH /api/me/` write step.

## Backend half

None. `User.theme_config` still defaults to `{}` (migration unchanged);
`UserSerializer` injects no server-side defaults — "a key never set by the
user is simply absent, no defaults injected server-side" ([[API]]). This
entry changes only frontend-side fallback constants and CSS; no `[[API]]`
row, no migration.

## Error handling

Unchanged from [[bdd-06-profile-theming]] for the `/profile` save path. This
entry adds no new failure mode — a malformed/absent `theme` cookie already
resolves to `{}` and then to `DEFAULTS`, which is exactly the mechanism this
entry retunes, not a new code path.

## Shadow-test spec

- Request `/` with no cookie → `<html class="dark" data-bg-preset="melt">`
  in the raw response body, provable without a browser
  (`frontend/tests/smoke.test.ts`).
- `computeThemeSSRAttrs(null)` → `{ htmlClass: "dark", dataBgPreset: "melt",
  style: "" }` (`frontend/tests/theme.test.ts`, DEFAULTS-relative assertion).
- Request `/showcase/components/` → response body contains markers for all 9
  `ui/` groups plus a `ThemeModeToggle` gallery section.
- Visual fidelity to melt-ui.com's actual dot grid/fade rendering is NOT
  provable by `bun:test` (no DOM/computed-style layer) — that confirmation
  is `kodex`-only, interactive, via the `chrome-devtools` MCP
  ([[AGENTS]]/[[DEVELOPMENT-LOOP]]'s smoke-test rule). This entry stays
  `draft` until that pass runs, same "until a project's shadow-test runner
  exists, this entry may reach `building`, never `shipped`" caveat
  [[bdd-06-profile-theming]] already states.
