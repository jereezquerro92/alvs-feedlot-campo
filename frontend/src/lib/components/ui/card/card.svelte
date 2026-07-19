<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { cn } from "$lib/utils";
  let { class: className = undefined, children, ...rest }: {
    class?: string; children?: import("svelte").Snippet; [key: string]: unknown;
  } = $props();
</script>

<div
  class={cn(
    "rounded-xl border bg-card text-card-foreground shadow flex flex-col gap-6 py-6",
    className,
  )}
  {...rest}
>
  {@render children?.()}
</div>
