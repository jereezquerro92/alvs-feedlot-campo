<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Zero-hydration paragraph for gallery slot bodies. Keeps raw <p> out of .astro
  pages ([[COMPONENTIZATION]] / adr-52 r9). Mounts with zero props (adr-22 r1).
-->
<script lang="ts">
  let {
    text = "",
    muted = false,
  }: {
    text?: string;
    muted?: boolean;
  } = $props();
</script>

<p class={muted ? "text-sm text-muted-foreground" : undefined}>{text}</p>
