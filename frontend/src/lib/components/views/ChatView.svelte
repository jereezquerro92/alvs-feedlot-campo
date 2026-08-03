<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  No `bg-canvas` here: the `melt` bgPreset paints `body` ([[DESIGN-SYSTEM]]
  "The Melt preset"), and an opaque `<main>` background would occlude it —
  same reasoning as ProfileView. The slotted ChatUI island fills the canvas.
-->
<!-- Flex column so the slotted ChatUI (`flex-1`, no longer `min-h-screen` of
     its own) takes the full canvas height from here. -->
<main class="relative flex min-h-screen w-full flex-col">
  <slot />
</main>
