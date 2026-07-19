<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { cn } from "$lib/utils";
  let { class: className = undefined, src = undefined, alt = "", ...rest }: {
    class?: string; src?: string; alt?: string; [key: string]: unknown;
  } = $props();
</script>

<img {src} {alt} class={cn("aspect-square size-full", className)} {...rest} />
