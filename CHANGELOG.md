# Changelog

## [Unreleased]

- group: oidc-immutable-sub
  priority: high
  commit: pending
  changes:
    - fix(infra): gha-deploy-prod trust entry rewritten to GitHub's immutable OIDC subject format — the v1 history reset recreated the repo past the 2026-07-15 cutoff, so the name-only sub no longer matched and STS denied AssumeRoleWithWebIdentity
    - fix(infra): BedrockGateNovaMicroInvoke statement added to gha-deploy-prod-policy — the bedrock-live gate invokes Nova Micro as the deploy role and the grant was missing since the gate landed
    - docs: GH.md immutable-subject section (format, cutoff, live prefix lookup); INFRASTRUCTURE.md CI/CD line; INVENTORY.md shared-attachment mutations recorded
    - docs(adr): new adr-23-oidc-immutable-subject-claim — additive to adr-08 rule 9 (adr-21/adr-22 pattern); immutable subject format mandatory for post-cutoff repos, trust entries re-derived on repo recreate/rename
    - chore(harness): kdx-aws-iam skill documents the immutable subject format
    - chore(gh): fixed label set recreated on the reborn repo; GitHub default labels outside the set removed
    - Closes #1.

## [v1.0.0] - 2026-07-19
The template goes public. First public release: the full working baseline — Astro 7 SSR + Svelte frontend, Django 6 + DRF backend, two-tier router, Cognito auth, M365 Graph capability, the vendored harness, and the complete docs vault. Git history starts here by design; the pre-v1 history is preserved in a private archive. Entries below record the work that led to this baseline; their PR/issue references (`#N`) point to the pre-v1 tracker and are kept as historical text.

- group: cloud-setup-bun-prearm
  priority: normal
  commit: a86693b
  changes:
    - fix(cloud): best-effort pre-warm of frontend bun deps in cloud_setup before service build

- group: agentr-triage-fix-single-retry
  priority: high
  commit: c92c829
  changes:
    - fix(harness): agentR single-retry wrapper guards triage-and-fix nodes against StructuredOutput null flake (issue #346)
    - chore(harness): distinct-label retry in agentR validates both node types match before allowing retry

- group: agentr-mutating-no-retry
  priority: high
  commit: c318efa
  changes:
    - fix(harness): agentR must not auto-retry hero-build and bard nodes — mutating operations with git/GitHub side effects run only once
    - refactor(harness): hero-build and bard now use plain agent() with clean abort-on-null, split bidirectionally enforced by validate.mjs
    - docs(harness): cast.md documents retry vs non-retry node split and its rationale (fixes #359)

- group: tier3-overlay-data
  priority: normal
  commit: pending
  changes:
    - feat(components): HoverCard — Melt-builder component (overlay/), tokenized, zero-prop-safe per adr-22
    - feat(components): Collapsible — hand-rolled custom component (data/), adr-04 rule 8 last-resort, tokenized, zero-prop-safe per adr-22, expand/collapse state toggle
    - feat(components): Tree — hand-rolled custom component (data/), adr-04 rule 8 last-resort, tokenized, zero-prop-safe per adr-22, hierarchical node structure with expand/collapse
    - feat(frontend): HoverCardDemo.svelte, CollapsibleDemo.svelte, TreeDemo.svelte (showcase/), wired into pages/showcase/components.astro (client:load) and ShowcaseGalleryView.svelte overlay/data sections
    - feat(i18n): gallery_hover_card, demo_hover_card_trigger/content keys; gallery_collapsible, demo_collapsible_trigger/content keys; gallery_tree, demo_tree_root/item keys added to src/i18n/messages/es.ts
    - docs: COMPONENTIZATION.md + GLOSSARY.md updated with HoverCard + Collapsible + Tree component rows
    - Closes #235.

- group: tier3-nav-menus
  priority: normal
  commit: pending
  changes:
    - feat(frontend): ContextMenu.svelte — Melt-builder component (nav/), roving-focus menu semantics, tokenized, zero-prop-safe per adr-22
    - feat(frontend): Menubar.svelte — Melt-builder component (nav/), horizontal menu bar with roving focus per ARIA menubar pattern, tokenized, zero-prop-safe per adr-22
    - feat(frontend): TableOfContents.svelte — custom component (nav/), scrolling index to page sections, zero-prop-safe per adr-22
    - feat(frontend): ContextMenuDemo.svelte, MenubarDemo.svelte, TableOfContentsDemo.svelte (showcase/), wired into pages/showcase/components.astro (client:load) and ShowcaseGalleryView.svelte nav section
    - feat(i18n): gallery_context_menu, demo_context_menu_trigger/item keys; gallery_menubar, demo_menubar_file/edit/help/item keys; gallery_table_of_contents, demo_toc_section keys added to src/i18n/messages/es.ts
    - docs: COMPONENTIZATION.md + GLOSSARY.md updated with ContextMenu + Menubar + TableOfContents component rows
    - Closes #233.

- group: slider-toggle-group-showcase
  priority: normal
  commit: pending
  changes:
    - feat(frontend): Slider — Melt-builder component (form/), tokenized, zero-prop-safe per adr-22
    - feat(frontend): ToggleGroup — composes Melt Toggle (form/), tokenized, zero-prop-safe per adr-22
    - feat(frontend): SliderDemo.svelte (showcase/), wired into pages/showcase/components.astro (client:load) and ShowcaseGalleryView.svelte form section
    - feat(frontend): ToggleGroupDemo.svelte (showcase/), wired into pages/showcase/components.astro (client:load) and ShowcaseGalleryView.svelte form section
    - feat(i18n): gallery_slider, demo_slider_label/value keys and gallery_toggle_group, demo_toggle_group_label keys added to src/i18n/messages/es.ts
    - docs: COMPONENTIZATION.md + GLOSSARY.md updated with Slider + ToggleGroup component rows
    - Closes #231.

- group: calendar-showcase
  priority: normal
  commit: pending
  changes:
    - feat(components): Calendar — hand-rolled custom component (form/), adr-04 rule 8 last-resort path, tokenized, zero-prop-safe per adr-22, month grid with date selection
    - feat(components): RangeCalendar — hand-rolled custom component (form/), adr-04 rule 8 last-resort path, tokenized, zero-prop-safe per adr-22, month range selection with start/end dates
    - feat(frontend): CalendarDemo.svelte (showcase/), wired into pages/showcase/components.astro (client:load) and ShowcaseGalleryView.svelte form section
    - feat(frontend): RangeCalendarDemo.svelte (showcase/), wired into pages/showcase/components.astro (client:load) and ShowcaseGalleryView.svelte form section
    - feat(i18n): gallery_calendar, demo_calendar_month/year/day keys and gallery_range_calendar, demo_range_calendar_month/year keys added to src/i18n/messages/es.ts
    - docs: COMPONENTIZATION.md + GLOSSARY.md updated with Calendar + RangeCalendar component rows
    - Closes #229.

- group: scroll-area-showcase
  priority: normal
  commit: pending
  changes:
    - feat(components): ScrollArea — hand-rolled custom component (overlay/), no Melt builder in melt 0.44, tokenized, zero-prop-safe per adr-22, scrollable div with styled scrollbar
    - feat(frontend): ScrollAreaDemo.svelte (showcase/), wired into pages/showcase/components.astro (client:load) and ShowcaseGalleryView.svelte overlay section
    - feat(i18n): gallery_scroll_area, demo_scroll_area_content keys added to src/i18n/messages/es.ts
    - docs: COMPONENTIZATION.md + GLOSSARY.md updated with ScrollArea component rows
    - Closes #227.

- group: tags-input-showcase
  priority: normal
  commit: pending
  changes:
    - feat(components): TagsInput — hand-rolled fallback (form/), Melt lacks TagsInput builder (adr-04 rule 8 last-resort), tokenized, zero-prop-safe per adr-22, removes/adds tags via input or pill close button
    - feat(frontend): TagsInputDemo.svelte (showcase/), wired into pages/showcase/components.astro (client:load) and ShowcaseGalleryView.svelte form section
    - feat(i18n): gallery_tags_input, demo_tags_input_group/label/add keys added to src/i18n/messages/es.ts
    - docs: COMPONENTIZATION.md + GLOSSARY.md updated with TagsInput component rows
    - Closes #223.

- group: pin-input-showcase
  priority: normal
  commit: pending
  changes:
    - feat(components): PinInput — Melt-builder component (form/), tokenized, zero-prop-safe per adr-22, 6-digit 2FA gate with onComplete no-op default
    - feat(frontend): PinInputDemo.svelte (showcase/), wired into pages/showcase/components.astro (client:load) and ShowcaseGalleryView.svelte form section
    - feat(i18n): gallery_pin_input, demo_pin_input_group/label/clear/confirmed keys added to src/i18n/messages/es.ts
    - docs: COMPONENTIZATION.md + GLOSSARY.md updated with PinInput component rows
    - Closes #221.

- group: pagination-showcase
  priority: normal
  commit: pending
  changes:
    - feat(components): Pagination — hand-rolled custom component (data/), adr-04 rule 8 last-resort path, tokenized, zero-prop-safe per adr-22
    - feat(frontend): PaginationDemo.svelte (showcase/), wired into pages/showcase/components.astro (client:load) and ShowcaseGalleryView.svelte data section
    - feat(i18n): gallery_pagination, demo_pagination_nav/prev/next keys added to src/i18n/messages/es.ts
    - docs: COMPONENTIZATION.md + GLOSSARY.md updated with Pagination component rows
    - Closes #219.

- group: palette-ratification
  priority: normal
  commit: pending
  changes:
    - docs(design-system): ratify rationed-orange palette (#178 palette note)

- group: popover-showcase
  priority: normal
  commit: pending
  changes:
    - feat(components): Popover — Melt-builder component (overlay/), tokenized, zero-prop-safe per adr-22
    - feat(frontend): PopoverDemo.svelte (showcase/), wired into pages/showcase/components.astro (client:load) and ShowcaseGalleryView.svelte overlay section
    - feat(i18n): gallery_popover, demo_popover_trigger/empty/quote/author keys added to src/i18n/messages/es.ts
    - docs: COMPONENTIZATION.md + GLOSSARY.md updated with Popover component rows
    - Closes #213.

- group: progress-showcase
  priority: normal
  commit: pending
  changes:
    - feat(components): Progress — Melt-builder component (feedback/), display-only, tokens-only, invocation with zero props per adr-22
    - feat(frontend): Progress exported from feedback/index.ts; wired into ShowcaseGalleryView.svelte + pages/showcase/components.astro with demo value 62/100
    - feat(i18n): gallery_progress, demo_progress_label keys added to src/i18n/messages/es.ts
    - Closes #211.

- group: dropdown-roving-tabindex
  priority: normal
  commit: pending
  changes:
    - fix(frontend): DropdownMenu.svelte — WAI-ARIA menu roving tabindex; exactly one item (the last-focused, enabled one) at tabindex 0, all others at -1, disabled items excluded; arrow/typeahead/mouse/open-focus all converge on the same `focusedIndex` state via each item's `onfocus`
    - Closes #208.

- group: dropdown-menu-showcase
  priority: normal
  commit: pending
  changes:
    - feat(frontend): DropdownMenu (nav/) + DropdownMenuDemo (showcase/) — Tier-2 nav component, Melt Popover primitive + hand-rolled roving-focus/typeahead menu semantics (no Melt Dropdown Menu builder in melt 0.44)
    - test(frontend): smoke coverage for the dropdown menu showcase entry
    - docs: BDD-09 dropdown-menu-showcase, COMPONENTIZATION nav/showcase rows, GLOSSARY dropdown-menu row wording fixed to match the Popover-based build
    - chore(harness): live-doc block re-synced on DropdownMenu.svelte, docs/CODEMAP.md regenerated
    - Closes #207. Refs #178.

- group: design-system-tokens
  priority: normal
  commit: b750e7b
  changes:
    - feat(design-system): orange OKLCH palette (--primary hue 45), warm-tinted neutrals, financial-state tokens (--success/--warning/--negative + -foreground), dark mode pairs, melt dots 1.5rem→2rem, white fade-band fix, user-select:none, px→rem

- group: componentization
  priority: normal
  commit: b750e7b
  changes:
    - feat(components): taxonomy primitives (primitives/, ui/, data/, dashboard/, chat/, auth/, overlay/); 9 Melt-first components (DataTable, NumericValue, StatusBadge, ChipFilterBar, MetricTile/MetricTileStrip, EntityCard/EntityGrid/SummaryCard); ADR-15-compliant ChatUI (ChatUI/ChatComposer/ChatMessageList); SOLID overlays (Dialog/Drawer/Accordion); vendored ui/table
    - feat(auth-ux): shared authGate.ts + "denied" banner on index/chatui/profile; showcase pages made PUBLIC (no role gate, by design)

- group: docs-adr
  priority: normal
  commit: b750e7b
  changes:
    - docs(adr): adr-04 in-place edit (owner-consented) — rule 8 Melt-first, rule 9 componentization
    - docs: new COMPONENTIZATION.md + component index; GLOSSARY rows (financial tokens, componentization); DESIGN-SYSTEM palette/dot/unit updates; MELT-UI/FRONTEND Melt-first flips

- group: harness
  priority: normal
  commit: b750e7b
  changes:
    - chore(harness): kdx-astro-7 flipped Melt-first + new references/melt-ui.md + rem/hex/OKLCH rules
    - chore(harness): live-doc blocks re-synced (26 files), docs/CODEMAP.md regenerated; kdx-live-doc manifest ChatInput path fix

- group: melt-ui-user-theming
  priority: high
  commit: pending
  changes:
    - feat(backend): User.theme_config JSONField (mig 0005), strict DRF validation (closed blob, mode/bgPreset enums, sanitized colors + radius regex), `theme` cookie set on login + PATCH /api/me/
    - test(backend): theme config tests in backend/apps/users/
    - feat(frontend): melt builders (ThemeModeToggle, ThemeCard preset), theme.ts, no-flash SSR (Base.astro), melt dotted-bg preset (app.css), /profile island
    - docs(design-system): ADR-04 r8 — zero-styling → variable-driven theming
    - docs: MELT-UI.md new, API.md /api/me/ updated, GLOSSARY + REQUIREMENTS entries, BDD-06 + TDD-01, live-doc + CODEMAP synced
    - Resolves #136, #137.

- group: changelog-router-tests
  priority: high
  commit: 426151c
  changes:
    - test(router): remove test_cognito_groups_claim_never_grants_access (bare non-assert + duplicate)
    - test(router): rewrite test_route_utterance_no_boto3_or_network_import to sys.modules absence check at import time (ADR-16)
    - test(router): hard-reject writes audit row with raw off-menu choice (ADR-15)
    - test(router): gated intent named by model is still hard-rejected (ADR-15 permission filtering precedes inference)
    - test(router): menu_offered in audit row excludes gated intents (ADR-15)
    - test(router): fully-gated user receives only NO_MATCH/ESCALATE outcomes (ADR-15)

- group: changelog-superadmin
  priority: high
  commit: d99440e
  changes:
    - feat(backend): idempotent bootstrap_admin management command creates/updates superadmin from DJANGO_SUPERUSER_EMAIL/PASSWORD env vars
    - feat(infra): bootstrap_admin wired into backend/Dockerfile boot sequence (after migrate, before ASGI)
    - docs(variables): DJANGO_SUPERUSER_EMAIL/PASSWORD documented, sourced from Secrets Manager alvs/<env>/<project>/django
    - docs(glossary): bootstrap_admin row added
    - docs(backend): bootstrap_admin bootstrap sequence documented
    - test(backend): bootstrap_admin tests in backend/apps/users/test_bootstrap_admin.py

## [v0.4.0] - 2026-07-14
Authenticated session UI: Google-only login, home session badge, shared SessionBadge/AuthPanel components, spotlight background, ChatInput aesthetic polish, and the userInfo fix for the Google avatar. Tagged from `prod` (4d2fc9e), which already carries all the code below; the doc-only findings batch that follows lands on `main`.

- group: avatar-from-userinfo
  priority: high
  commit: f1a1a87
  changes:
    - fix(backend): the Google profile picture never rendered because Cognito's ID token does not carry the picture claim — the value lives only in Cognito's /oauth2/userInfo response (the Cognito side was already correct: Google IdP maps picture->picture, the pool user holds the real lh3.googleusercontent.com URL, and the app client can read it, verified against AWS). CallbackView now makes a best-effort GET to /oauth2/userInfo with the access token and merges the response into the verified ID-token claims before mirroring, so picture reaches the User row through the existing path. Failure is non-fatal: userInfo erroring or timing out logs and lets the login proceed, degrading to the initials fallback — login is never sacrificed for an avatar. Same mechanism a prior kodexArg project (SROA) proved in production, without adopting its django-allauth dependency
    - docs: docs/API.md + docs/AUTH.md updated in the same batch (adr-03 rule 3); astro-drf-aws-api guardian verdict: valid
- group: home-logout
  priority: normal
  commit: f1a1a87
  changes:
    - feat(frontend): the home page's SessionBadge gains a logout control posting to the existing POST /accounts/logout/
    - refactor(frontend): CSRF-token logic already in AuthPanel extracted to shared frontend/src/lib/csrf.ts rather than duplicated
- group: google-only-login
  priority: high
  commit: c10dd4d
  changes:
    - feat(backend): /accounts/login/ now sends identity_provider=Google to Cognito's /oauth2/authorize, skipping the hosted-UI chooser so users land directly on Google's account picker; email/password becomes unreachable (owner-directed). Cognito remains the sole authenticator — Google is a federated IdP inside the user pool, so no ADR change (astro-drf-aws-adr guardian verdict: compliant)
    - docs(bdd): new entry docs/bdds/bdd-03-google-only-login.md
    - docs: docs/AUTH.md + docs/API.md updated in the same batch
- group: login-error-template
  priority: normal
  commit: 54abe9f
  changes:
    - fix(backend): unconfigured Cognito no longer builds a broken authorize URL or dumps a raw 500 — LoginView renders a minimal template (users/cognito_not_configured.html, status 500) naming only the missing COGNITO_* variable names, never their values
    - fix(backend): CallbackView now logs exceptions (logger.exception) instead of silently swallowing every failure
- group: auth-componentization
  priority: normal
  commit: c86b41a
  changes:
    - feat(frontend): SessionBadge.svelte (avatar + email pill / Log in) and AuthPanel.svelte (logged-in identity + group badges + logout) extracted as vendored components, shared by index.astro and showcase.astro
    - fix(frontend): showcase.astro's Auth section, deleted by 37bd715, is restored — as a component, not a revert
    - fix(frontend): the long-standing failing "Sample Card" smoke test is fixed at its root, not weakened
- group: login-ux-polish
  priority: normal
  commit: c86b41a
  changes:
    - fix(frontend): email in a white pill, softened card border, avatar fallback given real contrast against the spotlight (its bg-muted was the same lightness as the spotlight highlight and disappeared)
- group: home-page-base-layout
  priority: critical
  commit: 4f7bf40
  changes:
    - fix(frontend): index.astro rendered its own <html>/<body> and never used Base.astro, the only file importing styles/app.css; the home page therefore loaded no Tailwind or theme CSS at all and every utility class on it was inert (a pre-existing defect on main, invisible to the test suite because tests assert markup strings, not rendered styles). index.astro now renders through Base.astro.
- group: home-session-badge
  priority: normal
  commit: 8582b19
  changes:
    - feat(frontend): home page renders the logged-in user's Google profile picture + display name, top-center, via SSR call to /api/me/ (recovers cookie-forwarding fetch pattern regressed away in 37bd715); anonymous visitors get a Log in affordance
    - feat(backend): mirror OIDC picture standard claim onto User model — new field, migration 0003, serializer update, docs/API.md response-shape row (same batch per adr-03 rule 3)
    - docs(bdd): new entry docs/bdds/bdd-02-home-session-badge.md
    - test(frontend): smoke.test.ts now asserts both authenticated (real <img src>) and anonymous branches, replacing prior tolerance that let this regression ship unnoticed
- group: spotlight-background
  priority: normal
  commit: 7e19aae
  changes:
    - feat(frontend): page-wide spotlight background over the gray canvas in frontend/src/styles/app.css — two theme tokens (--spotlight-highlight oklch(0.975 0.012 95), a warm lifted tone deliberately not #fff; --spotlight-shadow oklch(0.8 0 0)) composed as a radial highlight across the upper viewport plus a linear falloff darkening the bottom third
- group: adr-00-controlled-edition
  priority: normal
  commit: 88be5d2
  changes:
    - chore(adr): adr-00 rule 4 — permit in-place edition for cosmetic changes or owner consent
- group: chatinput-lupa-polish
  priority: normal
  commit: fc3714c
  changes:
    - fix(frontend): ChatInput lupa polish — fix FOUC by adding explicit SVG width/height (lupa 32×32, send caret 16×16), enlarge lupa (size-6→size-8), reposition left (pl-2 pr-5), replace with rounder magnifying-glass glyph (lens r=8 + longer handle)
- group: premium-chatinput-aesthetic
  priority: high
  commit: 152409f
  changes:
    - feat(frontend): ChatInput full aesthetic rebuild — elevation shadow, card gradient, tokenized colors, enlarged magnifier, caret send button, pixel-aligned placeholder
    - feat(frontend): update showcase canvas background to bg-canvas token
    - feat(styles): add --canvas token (oklch 0.94 light / 0.115 dark) with theme awareness
- group: disable-dev-toolbar
  priority: normal
  commit: 4494340
  changes:
    - chore(frontend): disable Astro dev toolbar in devToolbar config
- group: prod-networking-fixes
  priority: critical
  commit: ff9549c
  changes:
    - fix(infra): SG self-referencing ingress rule tcp/8000 (sgr-01fbf972cc0bba98b) for frontend→backend via Cloud Map
    - fix(infra): ALLOWED_HOSTS must include Cloud Map hostname backend.astro-drf-aws-prod.local
    - docs(inventory): SG mutation recorded — self-rule for frontend SSR to backend
    - docs(infrastructure): ALLOWED_HOSTS requirement + Cloud Map security group rule
    - docs(variables): ALLOWED_HOSTS prod value requirement documented
- group: docs-m365-doctrine-batch
  priority: normal
  commit: b925ff4
  changes:
    - docs(glossary): m365, hello, world rows
    - docs(adrs): adr-13-m365-graph — app-only client_credentials capability
    - docs(variables): MSGRAPH_TENANT_ID, MSGRAPH_CLIENT_ID, MSGRAPH_CLIENT_SECRET
    - docs(api): GET /api/m365/hello, GET /api/m365/world endpoints + contracts
    - docs(requirements): msal 1.37.0, httpx 0.28.1
    - docs(prd): roadmap item 4 — M365 hello/world
    - docs(cache): Layer-3 example line
    - docs(env): .env.example MSGRAPH names
- group: feat-m365-backend-app
  priority: high
  commit: 7979d45
  changes:
    - feat(m365): new app apps/m365 with app-only Graph client
    - feat(m365): msal client_credentials flow + httpx Graph v1.0 calls
    - feat(m365): hardcoded site/workbook constants, first-worksheet resolution
    - feat(m365): 60s TTL per-process cell cache, Layer-3 caching
    - feat(m365): HelloView/WorldView — AllowAny, text/plain, no-store headers
    - feat(m365): clean 502/503 error taxonomy
    - feat(m365): settings/urls wiring, 5 passing tests
    - chore(backend): pyproject.toml + uv.lock sync
- group: feat-frontend-home-page
  priority: normal
  commit: b9327cd
  changes:
    - feat(frontend): plain white SSR home page index.astro
    - feat(frontend): fetch m365 hello/world words + template icon
    - docs(bdd): bdd-01-plain-home-page — first BDD entry
    - test(frontend): smoke.test.ts updated
- group: feat-frontend-home-page-v2
  priority: normal
  commit: 8fb2ad3
  changes:
    - feat(frontend): centered shadcn Button + Card home page layout
    - feat(frontend): Button links to /showcase/, Card holds M365 words as rows
    - docs(bdd): bdd-01-plain-home-page updated — design-system compliance
    - test(frontend): smoke.test.ts updated to match new structure
- group: feat-infra-msgraph-secrets-prod
  priority: high
  commit: cbf2866
  changes:
    - feat(infra): MSGRAPH_TENANT_ID/CLIENT_ID/CLIENT_SECRET in prod task definition
    - feat(infra): SECRET_MSGRAPH Secrets Manager wiring in deploy-prod.yml
    - docs(inventory): msgraph ephemeral secret tracked with adr-12 tags
- group: feat-frontend-showcase-hub-chatui
  priority: normal
  commit: 37bd715
  changes:
    - feat(frontend): showcase hub — index linking /showcase/components/ and /showcase/chatui/
    - feat(frontend): components gallery — shadcn components (Typography, Buttons, Badges, Form, Alert, Card) with Separator rules
    - feat(frontend): chatui canvas — full-viewport soft light-gray base for ChatInput island
    - feat(frontend): ChatInput island — Svelte 5, bottom-pinned pill, typewriter placeholder cycling, auto-grow textarea
- group: stage3-run-record-backfill
  priority: normal
  commit: a79cacc..9e7f2db
  changes:
    - ci(deploy): D1 — deploy-prod.yml, prod-only OIDC deploy (a79cacc, #38)
    - feat(frontend): C2 — /showcase design system + / redirect, bdd-01/bdd-02 (67ad374, #39)
    - docs(inventory): gha-deploy-prod trust entry applied, B2.6 attachment complete (85ce7d8)
    - docs(plan): Annex L — M1/T5+T6 green with caveats, console leg deferred to D4 (9061d64)
    - fix(ci): deploy-prod test job builds frontend before bun test, mirrors c669833 (cbe6eb1)
    - fix(ci): pin task SG by id — gha-deploy-prod lacks ec2:DescribeSecurityGroups (80b9802)
    - fix(backend): Cache-Control backstop for non-2xx responses, closes #42 (9e7f2db)
