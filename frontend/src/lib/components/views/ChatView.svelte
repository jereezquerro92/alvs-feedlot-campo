<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  No `bg-canvas` here: the `melt` bgPreset paints `body` ([[DESIGN-SYSTEM]]
  "The Melt preset"), and an opaque `<main>` background would occlude it —
  same reasoning as ProfileView. The slotted ChatUI island fills the canvas.
-->
<main class="relative min-h-screen w-full">
  <slot />
</main>
