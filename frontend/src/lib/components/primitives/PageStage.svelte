<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Centers a single primary control in the page body (initial pick / focus
  moments). Parent main must be a flex column with flex-1 so this can grow.
  Mounts with zero props and never throws ([[adr-22-showcase-ready-components]]
  rule 1). Width default is max-w-md — override via class.
-->
<script lang="ts">
  import type { Snippet } from "svelte";
  import { cn } from "$lib/utils";

  let {
    class: className = undefined,
    children,
  }: {
    class?: string;
    children?: Snippet;
  } = $props();
</script>

<div
  class={cn(
    "mx-auto flex w-full max-w-md flex-1 flex-col items-stretch justify-center gap-4",
    className,
  )}
>
  {@render children?.()}
</div>
