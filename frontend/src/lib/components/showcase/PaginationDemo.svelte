<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of data/Pagination — Pagination itself defaults to a
  safe single-page no-op state (adr-22 r1/r2), so this wrapper supplies the
  local $state page-count sample and the onPageChange wiring the gallery
  needs to show it actually paging, the same reason showcase/PopoverDemo.svelte
  exists.
-->
<script lang="ts">
  import { Pagination } from "$lib/components/data";

  let { pageCount }: { pageCount: number } = $props();

  let page = $state(1);
</script>

<Pagination {page} {pageCount} onPageChange={(next) => (page = next)} />
