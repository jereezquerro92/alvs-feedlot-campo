<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of overlay/HoverCard — `preview` is a Snippet, which
  Astro's slot mechanism cannot pass through, so the #snippet lives here
  (same reason showcase/PopoverDemo.svelte exists), supplying a realistic
  account-preview body instead of the component's empty-state fallback.
-->
<script lang="ts">
  import { HoverCard } from "$lib/components/overlay";

  let {
    triggerLabel,
    name,
    detail,
  }: {
    triggerLabel: string;
    name: string;
    detail: string;
  } = $props();
</script>

<HoverCard {triggerLabel}>
  {#snippet preview()}
    <p class="text-sm font-medium">{name}</p>
    <p class="mt-1 text-xs text-muted-foreground">{detail}</p>
  {/snippet}
</HoverCard>
