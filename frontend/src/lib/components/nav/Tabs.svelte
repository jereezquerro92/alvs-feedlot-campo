<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Tabbed navigation on the melt/builders Tabs ([[MELT-UI]]) — the builder
  owns roving focus, arrow-key navigation, and aria-selected wiring; this
  component is the styled shell.
-->
<script lang="ts" module>
  export type TabItem = {
    value: string;
    label: string;
    disabled?: boolean;
  };
</script>

<script lang="ts">
  import { Tabs } from "melt/builders";
  import { cn } from "$lib/utils";
  import type { Snippet } from "svelte";

  let {
    items = [],
    value = $bindable(items[0]?.value ?? ""),
    orientation = "horizontal",
    content,
    class: className = undefined,
  }: {
    items?: TabItem[];
    value?: string;
    orientation?: "horizontal" | "vertical";
    content?: Snippet<[TabItem]>;
    class?: string;
  } = $props();

  const tabs = new Tabs({
    value: () => value,
    onValueChange: (v) => (value = v),
    orientation: () => orientation,
  });
</script>

<div class={cn("flex gap-4", orientation === "vertical" ? "flex-row" : "flex-col", className)}>
  <div
    {...tabs.triggerList}
    class={cn("flex gap-1", orientation === "vertical" ? "flex-col border-r pr-2" : "border-b")}
  >
    {#each items as item (item.value)}
      {@const active = value === item.value}
      <button
        {...tabs.getTrigger(item.value)}
        disabled={item.disabled}
        class={cn(
          "cursor-pointer whitespace-nowrap px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground disabled:pointer-events-none disabled:opacity-50",
          "border-transparent",
          orientation === "vertical" ? "border-r-2 text-left" : "border-b-2",
          active && "border-primary text-foreground",
        )}
      >
        {item.label}
      </button>
    {/each}
  </div>
  <div class="flex-1">
    {#each items as item (item.value)}
      <div {...tabs.getContent(item.value)}>
        {@render content(item)}
      </div>
    {/each}
  </div>
</div>
