<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts" module>
  export type SummaryItem = { label: string; value: string };
</script>

<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import { cn } from "$lib/utils";

  let {
    title = "",
    items = [],
    class: className = undefined,
  }: {
    title?: string;
    items?: SummaryItem[];
    class?: string;
  } = $props();
</script>

<Card.Root class={cn("border-primary/40", className)}>
  <Card.Header>
    <Card.Title>{title}</Card.Title>
  </Card.Header>
  <Card.Content class="grid grid-cols-2 gap-4 pt-0 sm:grid-cols-3 md:grid-cols-4">
    {#each items as item (item.label)}
      <div class="flex flex-col gap-0.5">
        <span class="text-xs text-muted-foreground">{item.label}</span>
        <span class="text-lg font-semibold tabular-nums">{item.value}</span>
      </div>
    {/each}
  </Card.Content>
</Card.Root>
