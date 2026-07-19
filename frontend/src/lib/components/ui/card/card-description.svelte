<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { cn } from "$lib/utils";
  /** Size is a variant, not a class override — cn() has no conflict
   * merging, so a caller-supplied text-* class cannot beat the default
   * (same reasoning as Button's `bare` variant). */
  let { class: className = undefined, size = "sm", children, ...rest }: {
    class?: string; size?: "sm" | "xs"; children?: import("svelte").Snippet; [key: string]: unknown;
  } = $props();

  const sizeClass = { sm: "text-sm", xs: "text-xs" }[size];
</script>

<div class={cn(sizeClass, "text-muted-foreground", className)} {...rest}>
  {@render children?.()}
</div>
