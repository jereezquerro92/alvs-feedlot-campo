<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { cn } from "$lib/utils";
  let { class: className = undefined, orientation = "horizontal", ...rest }: {
    class?: string; orientation?: "horizontal" | "vertical"; [key: string]: unknown;
  } = $props();
</script>

<div
  role="separator"
  aria-orientation={orientation}
  class={cn(
    "shrink-0 bg-border",
    orientation === "horizontal" ? "h-[var(--hairline)] w-full" : "h-full w-[var(--hairline)]",
    className,
  )}
  {...rest}
></div>
