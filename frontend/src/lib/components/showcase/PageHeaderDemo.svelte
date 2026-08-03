<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Gallery demo of primitives/titles/PageHeader — title, subtitle, action buttons.
-->
<script lang="ts">
  import { PageHeader } from "$lib/components/primitives/titles";
  import { Button } from "$lib/components/ui/button";

  let {
    title = "",
    subtitle = "",
  }: {
    title?: string;
    subtitle?: string;
  } = $props();
</script>

<PageHeader {title} {subtitle}>
  {#snippet actions()}
    <Button variant="outline" size="sm">Outline</Button>
    <Button size="sm">Default</Button>
  {/snippet}
</PageHeader>
