<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[COMPONENTIZATION]]
     LIVE-DOC:END -->

<!--
  Panel heading strip for shell drawers (border-b + semibold title). FancyDrawer
  uses it when a title is supplied; the live feedlot FancyNav omits it. Kept as
  a standalone component for a future surface that needs a labeled panel head.
  Zero-prop safe (adr-22 r1): empty title renders an empty heading.
-->
<script lang="ts">
  let {
    title = "",
  }: {
    title?: string;
  } = $props();
</script>

<div class="flex items-center border-b border-border pb-3">
  <h2 class="truncate text-sm font-semibold text-foreground">{title}</h2>
</div>
