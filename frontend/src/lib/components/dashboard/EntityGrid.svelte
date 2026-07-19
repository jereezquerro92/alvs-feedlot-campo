<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { cn } from "$lib/utils";

  let {
    minWidth = "16rem",
    class: className = undefined,
    children,
  }: {
    /** Minimum card width before the grid reflows to fewer columns. */
    minWidth?: string;
    class?: string;
    children?: import("svelte").Snippet;
  } = $props();
</script>

<div
  class={cn("grid gap-4", className)}
  style={`grid-template-columns: repeat(auto-fill, minmax(min(${minWidth}, 100%), 1fr));`}
>
  {@render children?.()}
</div>
