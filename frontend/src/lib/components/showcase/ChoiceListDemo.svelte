<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Gallery demo of dashboard/ChoiceList — big-control pick rows with badges.
-->
<script lang="ts">
  import { ChoiceList, type ChoiceItem } from "$lib/components/dashboard";

  let {
    title = "",
    subtitle = "",
    items = [],
  }: {
    title?: string;
    subtitle?: string;
    items?: ChoiceItem[];
  } = $props();
</script>

<div class="mx-auto w-full max-w-md">
  <ChoiceList {title} {subtitle} {items} />
</div>
