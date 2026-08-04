<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[COMPONENTIZATION]]
     LIVE-DOC:END -->

<!--
  Compact ALVS brand mark (glyph disc + name + subtitle). Not mounted in the
  live FancyDrawer nav today — kept as a ready composition for a future shell
  surface. Zero-prop safe (adr-22 r1): defaults to ALVS + i18n subtitle.
-->
<script lang="ts">
  import { t } from "../../../i18n";

  let {
    mark = "A",
    name = "ALVS",
    subtitle = t("feedlot_brand_subtitle"),
  }: {
    mark?: string;
    name?: string;
    subtitle?: string;
  } = $props();
</script>

<div class="flex items-center gap-2.5 px-0.5">
  <span
    class="grid size-8 place-items-center rounded-xl text-sm font-black text-primary-foreground"
    style="background: var(--primary);"
    aria-hidden="true">{mark}</span
  >
  <div class="min-w-0 leading-tight">
    <div class="truncate text-xs font-bold tracking-wide text-foreground">{name}</div>
    <div class="truncate text-[0.65rem] text-muted-foreground">{subtitle}</div>
  </div>
</div>
