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

<td class={cn("p-2 align-middle [&:has([role=checkbox])]:pr-0", className)} {...rest}>
  {@render children?.()}
</td>
