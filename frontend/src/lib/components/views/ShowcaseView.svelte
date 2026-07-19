<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { SectionTitle } from "$lib/components/primitives/titles";

  type ShowcaseCopy = {
    title: string;
    intro: string;
  };

  let { copy = {} as ShowcaseCopy }: { copy?: ShowcaseCopy } = $props();
</script>

<main class="mx-auto max-w-3xl p-8 flex flex-col gap-6 items-start">
  <div class="flex flex-col gap-2">
    <SectionTitle as="h1">{copy.title}</SectionTitle>
    <p class="text-muted-foreground">{copy.intro}</p>
  </div>

  <slot />
</main>
