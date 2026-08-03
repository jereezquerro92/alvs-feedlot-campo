<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Gallery demo of nav/Breadcrumb — pill trail matching SessionBadge chrome.
-->
<script lang="ts">
  import { Breadcrumb, type BreadcrumbItem } from "$lib/components/nav";

  let {
    items = [],
    homeHref = "/feedlot/",
  }: {
    items?: BreadcrumbItem[];
    homeHref?: string;
  } = $props();
</script>

<Breadcrumb {items} {homeHref} />
