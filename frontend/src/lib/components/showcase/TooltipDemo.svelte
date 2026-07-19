<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of overlay/Tooltip — Tooltip's `trigger` prop is a
  parameterized Snippet<[Tooltip]>, which Astro's slot mechanism cannot pass
  through, so the #snippet lives here (same reason showcase/AlertDialogDemo.svelte
  exists) and this composition is dropped into the gallery page as a single
  client:load island.
-->
<script lang="ts">
  import { Tooltip } from "$lib/components/overlay";
  import { Button } from "$lib/components/ui/button";

  let {
    triggerLabel,
    content,
  }: {
    triggerLabel: string;
    content: string;
  } = $props();
</script>

<Tooltip {content}>
  {#snippet trigger(t)}
    <Button type="button" variant="outline" {...t.trigger}>{triggerLabel}</Button>
  {/snippet}
</Tooltip>
