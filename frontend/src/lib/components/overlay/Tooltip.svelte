<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Hover/focus hint on the melt/builders Tooltip ([[MELT-UI]]) — the builder
  owns open/close delays, the pointer grace area, and floating-ui placement
  via the native Popover API; this component is the styled shell.
-->
<script lang="ts" module>
  export type { Tooltip as TooltipBuilder } from "melt/builders";
</script>

<script lang="ts">
  import { Tooltip } from "melt/builders";
  import { cn } from "$lib/utils";
  import type { Snippet } from "svelte";

  let {
    content,
    trigger,
    side = "top",
    openDelay = 200,
    class: className = undefined,
  }: {
    content: string;
    /** Trigger element; receives the builder so you can spread `{...t.trigger}`. */
    trigger: Snippet<[Tooltip]>;
    side?: "top" | "bottom" | "left" | "right";
    openDelay?: number;
    class?: string;
  } = $props();

  const tooltip = new Tooltip({
    openDelay: () => openDelay,
    floatingConfig: { computePosition: { placement: side } },
  });
</script>

{@render trigger?.(tooltip)}

<div
  {...tooltip.content}
  class={cn(
    "z-50 max-w-xs rounded-md border bg-popover px-3 py-1.5 text-xs text-popover-foreground shadow-md",
    className,
  )}
>
  {content}
  <div {...tooltip.arrow} class="h-2 w-2"></div>
</div>
