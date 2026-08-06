---
title: adr-54-site-menu-lock-modes
type: adr
category: frontend
use_case: changing FeedlotFancyNav or FancyDrawer, adjusting shell menu visibility, lock or pin behavior, or the breakpoint that chooses rail vs drawer
created: 2026-08-05
modified: 2026-08-06
tags: [adr, frontend, shell, menu, fancy-nav]
---

# ADR-54 — site menu lock modes

## CONTEXT

> The site menu has two modes — locked rail and unlocked drawer — and one of them must always be reachable. A viewport that cannot host the rail does not get to hide the menu. Preference and selection are known before first paint so navigation never blanks the chrome.

## ASSERTIONS

1. The feedlot site menu has exactly two presentation modes: **locked** (permanent in-flow rail) and **unlocked** (floating FancyDrawer with a peek caret). The user chooses the preference; the shell mounts one preference at a time. Ownership of the components and the rail minimum width: [[COMPONENTIZATION]], [[DESIGN-SYSTEM]].
2. Locked mode is available only when the viewport meets the rail minimum width in [[DESIGN-SYSTEM]]. Below that width, the layout MUST present unlocked mode even if the lock preference is on; the preference may persist so the rail returns when the viewport fits again.
3. The menu is NEVER invisible: wherever the shell menu mounts, either the rail or the FancyDrawer peek caret is present and operable. A locked preference plus a CSS hide without an unlocked fallback is a defect. **The only condition on the menu is that the session has a role** ([[adr-20-authorization-lobby]] rule 1): no page, path, query parameter or selected entity is a precondition for the chrome. A client is per-link data — an unselected one scopes no link and suppresses nothing. Whether an individual *item* is shown is a separate question from whether the menu is shown, and it never resolves to hiding the menu.
4. The FancyDrawer peek caret toggles the drawer on click and tap as well as on mouse hover. When collapsed, the caret stays inside the drawer's hit box so pointer events reach it ([[COMPONENTIZATION]]).
5. Dock edge follows `theme_config.sidebarSide` ([[DESIGN-SYSTEM]], [[API]]).
6. Lock preference is a client chrome cookie (`nav_lock`), readable on SSR like the `theme` cookie, so the first byte of every navigation already knows locked vs unlocked. localStorage alone is not the source of truth. Mechanism: [[DESIGN-SYSTEM]].
7. The menu's runtime state is a closed FSM with three fields — preference (`locked`|`unlocked`), presentation (`rail`|`drawer`), and active item — resolved by `shell/nav-fsm`. Presentation is derived from preference alone and never stored; because both of its values are a menu, no FSM input can resolve to no menu (rule 3). The viewport band is **not** an FSM field: rule 2's floor is enforced by CSS at the rail minimum width over the pair rule 8 mounts, so nothing measured at runtime decides what renders. Active comes from the URL via `resolveShellNav` on SSR ([[COMPONENTIZATION]]).
8. When preference is locked, first paint may mount both the rail and the drawer and let CSS at the rail minimum choose which is visible, so a full navigation cannot flash unlocked while JavaScript catches up.

## FORBIDDEN

- **NEVER** hide the locked rail at a breakpoint without forcing unlocked FancyDrawer (rules 2–3). That pairing is how tablets lost the menu.
- **NEVER** leave the collapsed FancyDrawer caret outside the transformed element's hit box (rule 4). Paint without hit-testing is an invisible control.
- **NEVER** make lock preference depend on `onMount` / localStorage alone (rule 6). That blanks the locked rail on every Astro navigation until hydrate.
- **NEVER** gate the menu on a selected client, a path shape, or any query parameter (rule 3). The role is the only condition; a URL-shaped gate deletes the chrome on exactly the pages that carry no client and leaves the user no control to leave them by.
- **NEVER** reintroduce a runtime measurement into the FSM to choose the presentation (rule 7). Both presentations are a menu, CSS already enforces rule 2's floor, and a measured field can only start wrong and jump.

## REJECTED

- **A selected client as a precondition for the menu** — `Base.astro` mounted FancyNav only when the request URL already identified a client (numeric path `/feedlot/{id}/…` or `?client=`), on the reasoning that a menu of client-scoped links is meaningless without one. Retired on 2026-08-06, owner authorization in conversation ([[adr-00-discipline]] rule 8), because it contradicted rule 3 outright: `/feedlot/precios`, `/feedlot/usuarios`, `/profile/` and the component gallery rendered no chrome at all, and the nav's own route table stripped `?client=` on the way to those pages — so the menu disqualified itself and left no control to navigate back with. The component always tolerated a null client; only the layout refused. It would reopen only if the menu became entirely client-scoped, which rule 3 now forbids.
- **The viewport band as an FSM field** — `nav-fsm` carried a `viewport` (`mobile`|`tablet`|`desk`) resolved from two `matchMedia` listeners, and `resolvePresentation` took it as a second argument. Dropped on 2026-08-06 with the same authorization: it decided nothing, because rule 8 already mounts rail and drawer together and CSS at the rail minimum picks the visible one. Its only effect was that presentation started at a guessed `desk` until `onMount` corrected it — a hydration jump bought with two listeners and a three-value type. Rule 2's floor is unchanged; it is enforced where it always actually was, in CSS. It would reopen only if a presentation decision genuinely needed a measurement no media query can express.
- **`lg:` (64rem) as the locked-rail floor with a separate mobile overlay that nothing opened** — the prior shape. Rejected because lock-on below that floor rendered neither rail nor drawer. Reopens only if a dedicated, always-wired open control replaces the forced-drawer fallback.
- **localStorage-only pin read in `onMount`** — preference survived sessions but not SSR, so each link click painted unlocked then snapped to locked. Replaced by rule 6's `nav_lock` cookie. Would reopen only if the menu stopped being SSR-mounted.

## RELATED

### related adrs

- [[adr-52-frontend-and-design-system]] — frontend stack this menu sits in
- [[adr-22-showcase-ready-components]] — zero-prop mount for FancyNav and FancyDrawer
- [[adr-20-authorization-lobby]] — rule 1, the role that is the menu's only condition

### related files

- [[COMPONENTIZATION]] — `FeedlotFancyNav`, `FancyDrawer`, `NavLockToggle`, `shell/nav-fsm`
- [[DESIGN-SYSTEM]] — `sidebarSide`, the rail minimum width, and the `nav_lock` cookie
- [[API]] — `theme_config.sidebarSide` on `PATCH /api/me/`
