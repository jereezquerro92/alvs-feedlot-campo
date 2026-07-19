<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Click-triggered floating content on the melt/builders Popover ([[MELT-UI]])
  — the same float/anchor/dismiss primitive nav/DropdownMenu.svelte sits on,
  used here for its bare form: no roving-focus/typeahead menu semantics, just
  a self-rendering trigger Button and a styled content box (mirrors
  overlay/Tooltip.svelte's shell, not DropdownMenu's hand-rolled keyboard
  layer). `content` defaults to an i18n empty-state Snippet so a zero-prop
  invocation still renders without throwing (adr-22 r1) and fires no
  mutating call (adr-22 r2).
-->
<script lang="ts" module>
  export type { Popover as PopoverBuilder } from "melt/builders";
</script>

<script lang="ts">
  import { Popover } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";
  import type { Snippet } from "svelte";

  let {
    triggerLabel = t("demo_popover_trigger"),
    content,
    side = "bottom",
    class: className = undefined,
  }: {
    triggerLabel?: string;
    content?: Snippet;
    side?: "top" | "bottom" | "left" | "right";
    class?: string;
  } = $props();

  const popover = new Popover({
    floatingConfig: { computePosition: { placement: side } },
  });
</script>

<Button type="button" variant="outline" {...popover.trigger} class={className}>
  {triggerLabel}
</Button>
<div
  {...popover.content}
  class="z-50 w-72 rounded-md border border-border bg-popover p-4 text-popover-foreground shadow-md"
>
  {#if content}
    {@render content()}
  {:else}
    <p class="text-sm text-muted-foreground">{t("demo_popover_empty")}</p>
  {/if}
</div>
