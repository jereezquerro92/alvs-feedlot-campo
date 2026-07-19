<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of nav/Tabs — Tabs' `content` prop is a parameterized
  Snippet<[TabItem]>, which Astro's slot mechanism cannot pass through, so
  the #snippet lives here (same reason showcase/AlertDialogDemo.svelte
  exists) and this composition is dropped into the gallery page as a single
  client:load island.
-->
<script lang="ts">
  import { Tabs, type TabItem } from "$lib/components/nav";

  let {
    items,
    body,
  }: {
    items: TabItem[];
    /** Tab body text keyed by TabItem.value, i18n-supplied by the caller. */
    body: Record<string, string>;
  } = $props();
</script>

<Tabs {items}>
  {#snippet content(item)}
    <p class="text-sm text-muted-foreground">{body[item.value]}</p>
  {/snippet}
</Tabs>
