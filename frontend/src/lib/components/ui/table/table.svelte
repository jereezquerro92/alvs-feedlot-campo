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

<div class="relative w-full overflow-x-auto">
  <table class={cn("w-full table-fixed caption-bottom text-sm", className)} {...rest}>
    {@render children?.()}
  </table>
</div>
