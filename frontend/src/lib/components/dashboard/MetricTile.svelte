<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { cn } from "$lib/utils";
  import { Button } from "$lib/components/ui/button";
  import NumericValue from "$lib/components/data/NumericValue.svelte";

  let {
    label,
    value = undefined,
    currency = undefined,
    count = undefined,
    active = false,
    class: className = undefined,
    ...rest
  }: {
    label: string;
    /** Optional headline figure, rendered through NumericValue when present. */
    value?: number;
    /** Optional currency label for the figure; omit for a plain number. */
    currency?: string;
    /** Optional secondary count shown beside the label. */
    count?: number;
    active?: boolean;
    class?: string;
    [key: string]: unknown;
  } = $props();
</script>

<Button
  type="button"
  variant="bare"
  aria-pressed={active}
  class={cn(
    "flex min-w-[9rem] flex-col gap-1 rounded-lg border px-4 py-3 text-left",
    active
      ? "border-primary bg-primary/10 text-foreground"
      : "border-border bg-card text-card-foreground hover:bg-accent hover:text-accent-foreground",
    className,
  )}
  {...rest}
>
  <span class="flex items-center justify-between gap-2 text-xs font-medium text-muted-foreground">
    {label}
    {#if count !== undefined}
      <span class="tabular-nums">{count}</span>
    {/if}
  </span>
  {#if value !== undefined}
    <NumericValue {value} {currency} class="text-base" />
  {/if}
</Button>
