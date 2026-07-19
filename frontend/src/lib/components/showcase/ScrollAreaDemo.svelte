<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of overlay/ScrollArea — ScrollArea's `content` prop
  is a Snippet, which Astro's slot mechanism cannot pass through, so the
  #snippet lives here (same reason showcase/PopoverDemo.svelte exists),
  supplying a realistic long-list body instead of the component's
  empty-state fallback.
-->
<script lang="ts">
  import { ScrollArea } from "$lib/components/overlay";

  let {
    items,
  }: {
    items: string[];
  } = $props();
</script>

<ScrollArea>
  {#snippet content()}
    <ul class="flex flex-col gap-2 text-sm">
      {#each items as item, i (i)}
        <li>{item}</li>
      {/each}
    </ul>
  {/snippet}
</ScrollArea>
