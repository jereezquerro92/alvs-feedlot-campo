<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Constrained-height scroll container with a themed scrollbar, for drawer/chat
  long content. Melt 0.44 ships no ScrollArea builder ([[MELT-UI]] — same
  absence recorded for Pagination/DropdownMenu/TagsInput above), so the
  scroll box is hand-rolled here rather than delegated: native
  `overflow-y-auto` plus token-driven scrollbar colors. `content` defaults to
  an i18n placeholder Snippet so a zero-prop invocation still renders without
  throwing (adr-22 r1) and fires no mutating call (adr-22 r2).
-->
<script lang="ts">
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";
  import type { Snippet } from "svelte";

  let {
    content,
    maxHeight = "16rem",
    class: className = undefined,
  }: {
    content?: Snippet;
    maxHeight?: string;
    class?: string;
  } = $props();
</script>

<div
  class={cn(
    "scrollbar-themed overflow-y-auto rounded-md border border-border bg-popover p-4 text-popover-foreground",
    className,
  )}
  style={`max-height: ${maxHeight};`}
>
  {#if content}
    {@render content()}
  {:else}
    <p class="text-sm text-muted-foreground">{t("demo_scroll_area_empty")}</p>
  {/if}
</div>

<style>
  .scrollbar-themed {
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
  }

  .scrollbar-themed::-webkit-scrollbar {
    width: 0.5rem;
  }

  .scrollbar-themed::-webkit-scrollbar-track {
    background: transparent;
  }

  .scrollbar-themed::-webkit-scrollbar-thumb {
    background-color: var(--border);
    border-radius: 9999px;
  }
</style>
