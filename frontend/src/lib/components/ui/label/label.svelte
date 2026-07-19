<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { cn } from "$lib/utils";
  let { class: className = undefined, for: forId = undefined, children, ...rest }: {
    class?: string; for?: string; children?: import("svelte").Snippet; [key: string]: unknown;
  } = $props();
</script>

<label
  for={forId}
  class={cn(
    "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
    className,
  )}
  {...rest}
>{@render children?.()}</label>
