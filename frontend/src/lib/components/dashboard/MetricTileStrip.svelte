<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts" module>
  export type MetricTileData = {
    key: string;
    label: string;
    value?: number;
    currency?: string;
    count?: number;
  };
</script>

<script lang="ts">
  import { cn } from "$lib/utils";
  import MetricTile from "./MetricTile.svelte";

  let {
    tiles = [],
    activeKey = $bindable(""),
    class: className = undefined,
  }: {
    tiles?: MetricTileData[];
    /** The selected tile's key; clicking the active tile clears it back to "". */
    activeKey?: string;
    class?: string;
  } = $props();

  function toggle(key: string): void {
    activeKey = activeKey === key ? "" : key;
  }
</script>

<div class={cn("flex flex-wrap gap-3", className)}>
  {#each tiles as tile (tile.key)}
    <MetricTile
      label={tile.label}
      value={tile.value}
      currency={tile.currency}
      count={tile.count}
      active={activeKey === tile.key}
      onclick={() => toggle(tile.key)}
    />
  {/each}
</div>
