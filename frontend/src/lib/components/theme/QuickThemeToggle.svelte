<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Quick toggle housed in SessionBadge's ☰ menu (docs/bdds/bdd-07-melt-theme-sitewide.md):
  cookie-only mode persistence, deliberately decoupled from `/profile`'s ThemeCard, which
  is the only control that writes `theme_config` via `PATCH /api/me/`. Wraps
  ThemeModeToggle ([[MELT-UI]]) with zero edits to it — every other themed
  key (bgPreset, colors, radius) is untouched here and stays whatever the
  cookie already holds.
-->
<script lang="ts">
  import ThemeModeToggle from "$lib/components/theme/ThemeModeToggle.svelte";
  import { DEFAULTS, readThemeCookie, applyTheme, writeThemeCookie, type ThemeMode } from "$lib/theme";

  let mode = $state<ThemeMode>(readThemeCookie().mode ?? DEFAULTS.mode);

  function setMode(next: ThemeMode): void {
    mode = next;
    const merged = { ...readThemeCookie(), mode: next };
    applyTheme(merged);
    writeThemeCookie(merged);
  }
</script>

<ThemeModeToggle bind:mode={() => mode, setMode} />
