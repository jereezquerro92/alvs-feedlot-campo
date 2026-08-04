<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Quick theme row for SessionBadge's menu. Flips mode, applies live, writes
  the theme cookie; when `onPersist` is supplied (signed-in), the parent
  PATCHes theme_config so DB and cookie stay aligned.
-->
<script lang="ts">
  import { Toggle } from "melt/builders";
  import SessionMenuRow from "$lib/components/auth/SessionMenuRow.svelte";
  import {
    DEFAULTS,
    readThemeCookie,
    applyTheme,
    writeThemeCookie,
    type ThemeMode,
    type ThemeConfig,
  } from "$lib/theme";
  import { t } from "../../../i18n";

  let {
    onPersist,
  }: {
    /** Optional signed-in persist hook — parent PATCHes /api/me/. */
    onPersist?: (blob: ThemeConfig) => void | Promise<void>;
  } = $props();

  let mode = $state<ThemeMode>(readThemeCookie().mode ?? DEFAULTS.mode);

  function setMode(next: ThemeMode): void {
    mode = next;
    const merged = { ...readThemeCookie(), mode: next };
    applyTheme(merged);
    writeThemeCookie(merged);
    void onPersist?.(merged);
  }

  const toggle = new Toggle({
    value: () => mode === "dark",
    onValueChange: (isDark) => {
      setMode(isDark ? "dark" : "light");
    },
  });

  const label = $derived(mode === "dark" ? t("theme_mode_dark") : t("theme_mode_light"));
  const icon = $derived(mode === "dark" ? ("moon" as const) : ("sun" as const));
</script>

<SessionMenuRow
  {label}
  {icon}
  ariaLabel={t("theme_toggle_mode")}
  {...toggle.trigger}
/>
