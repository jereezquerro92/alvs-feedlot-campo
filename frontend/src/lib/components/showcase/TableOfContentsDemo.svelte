<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Component-gallery demo of nav/TableOfContents — sample sections that don't
  exist elsewhere on this page, so the component renders its plain link list
  with no active target to highlight (the gallery page has no matching
  headings to scroll to; that is expected here, not a defect).
-->
<script lang="ts">
  import { TableOfContents, type TableOfContentsItem } from "$lib/components/nav";

  let {
    items,
    label,
  }: {
    items: TableOfContentsItem[];
    label: string;
  } = $props();
</script>

<TableOfContents {items} {label} />
