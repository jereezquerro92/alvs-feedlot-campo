<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of primitives/CornerNavTriangle (issue #374).
  Not mounted site-wide. Containment matches HomeTriangleDemo.svelte:
  `[&_a]:!absolute` strips the component's own `position: fixed`,
  docking it inside this card instead of the viewport corner.
-->
<script lang="ts">
  import CornerNavTriangle from "$lib/components/primitives/CornerNavTriangle.svelte";
  import { t } from "../../../i18n";
</script>

<p class="text-sm text-muted-foreground">{t("demo_corner_nav_triangle_note")}</p>
<div class="relative h-24 w-24 overflow-hidden rounded-md border border-border [&_a]:!absolute">
  <CornerNavTriangle />
</div>
