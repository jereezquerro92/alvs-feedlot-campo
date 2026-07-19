<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  No `bg-canvas` here (unlike ChatView): the `melt` bgPreset paints `body`
  ([[DESIGN-SYSTEM]] "The Melt preset"), and an opaque `<main>` background
  would occlude it on the exact page that controls it.
-->
<script lang="ts">
  import { SectionTitle } from "$lib/components/primitives/titles";

  let { title, intro }: { title: string; intro: string } = $props();
</script>

<main class="flex min-h-screen w-full flex-col items-center gap-8 px-6 py-16">
  <div class="flex flex-col items-center gap-2 text-center">
    <SectionTitle as="h1">{title}</SectionTitle>
    <p class="text-muted-foreground">{intro}</p>
  </div>
  <div class="flex w-full max-w-4xl flex-col items-center gap-6 md:flex-row md:items-stretch md:justify-center lg:items-start">
    <slot />
  </div>
</main>
