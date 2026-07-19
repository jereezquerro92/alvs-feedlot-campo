<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of data/Collapsible — `content` is a Snippet, which
  Astro's slot mechanism cannot pass through, so the #snippet lives here
  (same reason showcase/PopoverDemo.svelte exists), supplying a realistic
  reconciliation-note body instead of the component's empty-state fallback.
-->
<script lang="ts">
  import { Collapsible } from "$lib/components/data";

  let {
    triggerLabel,
    body,
  }: {
    triggerLabel: string;
    body: string;
  } = $props();
</script>

<Collapsible {triggerLabel}>
  {#snippet content()}
    <p>{body}</p>
  {/snippet}
</Collapsible>
