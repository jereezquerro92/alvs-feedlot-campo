<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts" module>
  export type EntityStat = { label: string; value: string };
</script>

<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import StatusBadge from "$lib/components/data/StatusBadge.svelte";
  import { cn } from "$lib/utils";

  let {
    title,
    subtitle = undefined,
    stats = [],
    status = undefined,
    href = undefined,
    class: className = undefined,
    ...rest
  }: {
    title: string;
    subtitle?: string;
    stats?: EntityStat[];
    /** Status key handed to StatusBadge; omit for no badge. */
    status?: string;
    /** When set, the whole card becomes a link. */
    href?: string;
    class?: string;
    [key: string]: unknown;
  } = $props();
</script>

<svelte:element
  this={href ? "a" : "div"}
  {href}
  data-pressable={href ? "" : undefined}
  class={cn(href && "block focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring rounded-xl", className)}
  {...rest}
>
  <Card.Root class={cn(href && "transition-colors hover:border-primary/60")}>
    <Card.Header>
      <div class="flex items-start justify-between gap-3">
        <div class="flex flex-col gap-0.5">
          <Card.Title class="text-lg text-foreground/90">{title}</Card.Title>
          {#if subtitle}
            <Card.Description size="xs">{subtitle}</Card.Description>
          {/if}
        </div>
        {#if status}
          <StatusBadge {status} />
        {/if}
      </div>
    </Card.Header>
    {#if stats.length > 0}
      <Card.Content class="flex flex-col gap-1.5 pt-0">
        {#each stats as stat (stat.label)}
          <div class="flex items-center justify-between text-sm">
            <span class="text-muted-foreground">{stat.label}</span>
            <span class="tabular-nums font-medium">{stat.value}</span>
          </div>
        {/each}
      </Card.Content>
    {/if}
  </Card.Root>
</svelte:element>
