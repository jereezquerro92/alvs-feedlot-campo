<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Page-level header: SectionTitle (h1) + optional subtitle + optional actions.
  Replaces hand-rolled title flex rows. Pure presentation; mounts with zero
  props (empty title) and never throws ([[adr-22-showcase-ready-components]]
  rule 1). Copy arrives from the caller ([[LOCALIZATION]]).
-->
<script lang="ts">
  import type { Snippet } from "svelte";
  import { cn } from "$lib/utils";
  import SectionTitle from "./SectionTitle.svelte";

  let {
    title = "",
    subtitle = "",
    actions,
    class: className = undefined,
  }: {
    title?: string;
    subtitle?: string;
    /** Optional trailing controls (buttons, links) aligned to the title row. */
    actions?: Snippet;
    class?: string;
  } = $props();
</script>

<div
  class={cn(
    "flex flex-wrap items-end justify-between gap-3",
    className,
  )}
>
  <div class="flex min-w-0 flex-col gap-1">
    <SectionTitle as="h1">{title}</SectionTitle>
    {#if subtitle}
      <p class="text-sm text-muted-foreground">{subtitle}</p>
    {/if}
  </div>
  {#if actions}
    <div class="flex flex-wrap items-center gap-2">
      {@render actions()}
    </div>
  {/if}
</div>
