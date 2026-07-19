<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  A single-select chip row built on the melt/builders RadioGroup — the same
  headless-builder pattern as ThemeCard's bgPreset selector ([[MELT-UI]]).
  RadioGroup supplies roving-focus and aria-checked; the chips are the
  styled layer on top.
-->
<script lang="ts" module>
  export type ChipItem = { key: string; label: string; count?: number };
</script>

<script lang="ts">
  import { RadioGroup } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";

  let {
    chips = [],
    value = $bindable("all"),
    allKey = "all",
    allLabel = "All",
    showAll = true,
    label = "Filter",
    class: className = undefined,
  }: {
    chips?: ChipItem[];
    /** The selected chip key; defaults to the "all" sentinel. */
    value?: string;
    allKey?: string;
    allLabel?: string;
    showAll?: boolean;
    label?: string;
    class?: string;
  } = $props();

  const total = $derived(chips.reduce((sum, c) => sum + (c.count ?? 0), 0));
  const items = $derived(
    showAll ? [{ key: allKey, label: allLabel, count: total }, ...chips] : chips,
  );

  const group = new RadioGroup({
    value: () => value,
    onValueChange: (v) => (value = v),
    orientation: () => "horizontal",
  });
</script>

<div class="flex flex-col gap-1">
  <span {...group.label} class="sr-only">{label}</span>
  <div
    {...group.root}
    class={cn("flex gap-2 overflow-x-auto pb-1", className)}
  >
    {#each items as chip (chip.key)}
      {@const item = group.getItem(chip.key)}
      <Button
        type="button"
        variant="bare"
        {...item.attrs}
        class={cn(
          "flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border px-3 py-1 text-sm",
          item.checked
            ? "border-primary bg-primary/10 text-foreground"
            : "border-input bg-background text-muted-foreground hover:bg-accent hover:text-accent-foreground",
        )}
      >
        {chip.label}
        {#if chip.count !== undefined}
          <span class="tabular-nums text-xs opacity-70">({chip.count})</span>
        {/if}
      </Button>
    {/each}
  </div>
</div>
