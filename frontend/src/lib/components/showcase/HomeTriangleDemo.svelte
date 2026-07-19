<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of primitives/HomeTriangle (issue #255, spike;
  issue #282 fix) — the gallery may only ever hide/displace, never act
  (owner rule sharpening adr-22 rule 2): this instance is rendered with
  NEITHER `href` NOR `onHome`, so `resolveHomeTarget` falls to the `inert`
  branch and the component paints its safe, non-interactive `aria-hidden`
  span (adr-22 r1). The wrapping box gives the `position: fixed`
  viewport-corner shape a visible, non-confusing home inside the gallery
  card instead of docking to the real page corner.
-->
<script lang="ts">
  import HomeTriangle from "$lib/components/primitives/HomeTriangle.svelte";
  import { t } from "../../../i18n";
</script>

<p class="text-sm text-muted-foreground">{t("demo_home_triangle_note")}</p>
<div class="relative h-16 w-16 overflow-hidden rounded-md border border-border [&_span]:!absolute">
  <HomeTriangle />
</div>
