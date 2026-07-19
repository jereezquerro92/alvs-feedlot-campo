<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[MELT-UI]]
     LIVE-DOC:END -->

<!--
  The vendored Melt UI example ([[MELT-UI]] "Where this template uses it"):
  a fully custom control built with `melt/builders` — no shadcn-svelte/Bits
  UI equivalent ships this behavior (toggling `.dark` directly as part of
  its own state), per [[DESIGN-SYSTEM]]'s component-layering order.
-->
<script lang="ts">
  import { Toggle } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import { t } from "../../../i18n";
  import type { ThemeMode } from "$lib/theme";

  let {
    mode = $bindable<ThemeMode>("light"),
    disabled = false,
  }: { mode?: ThemeMode; disabled?: boolean } = $props();

  const toggle = new Toggle({
    value: () => mode === "dark",
    onValueChange: (isDark) => {
      mode = isDark ? "dark" : "light";
    },
    disabled: () => disabled,
  });
</script>

<Button
  type="button"
  variant="bare"
  {...toggle.trigger}
  aria-label={t("theme_toggle_mode")}
  class="inline-flex size-9 items-center justify-center rounded-md border border-input bg-background text-sm font-medium shadow-sm hover:bg-accent hover:text-accent-foreground"
>
  <span aria-hidden="true">{toggle.value ? "\u{1F319}" : "\u{2600}️"}</span>
</Button>
