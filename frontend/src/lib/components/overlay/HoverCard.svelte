<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Hover-triggered rich preview on the melt/builders Popover ([[MELT-UI]]) —
  melt 0.44 ships no dedicated Hover Card builder, so Popover supplies the
  float/anchor/dismiss plumbing (same absence-with-composition shape as
  nav/DropdownMenu.svelte) and this component adds hover semantics on top:
  `open` is driven by `mouseenter`/`mouseleave` on the trigger and content
  (moving the pointer from trigger to card keeps it open) plus `focusin`/
  `focusout` for keyboard users, so no click ever opens or closes it. A short
  close delay tolerates the pointer crossing the gap between trigger and
  card. `preview` defaults to an i18n empty-state Snippet so a zero-prop
  invocation still renders without throwing (adr-22 r1) and fires no
  mutating call (adr-22 r2).
-->
<script lang="ts" module>
  export type { Popover as HoverCardBuilder } from "melt/builders";
</script>

<script lang="ts">
  import { Popover } from "melt/builders";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";
  import type { Snippet } from "svelte";

  let {
    triggerLabel = t("demo_hover_card_trigger"),
    preview,
    side = "bottom",
    closeDelay = 150,
    class: className = undefined,
  }: {
    triggerLabel?: string;
    preview?: Snippet;
    side?: "top" | "bottom" | "left" | "right";
    closeDelay?: number;
    class?: string;
  } = $props();

  const hoverCard = new Popover({
    floatingConfig: { computePosition: { placement: side } },
  });

  let closeTimer: ReturnType<typeof setTimeout> | undefined;

  function cancelClose() {
    clearTimeout(closeTimer);
  }

  function scheduleClose() {
    clearTimeout(closeTimer);
    closeTimer = setTimeout(() => (hoverCard.open = false), closeDelay);
  }

  function open() {
    cancelClose();
    hoverCard.open = true;
  }
</script>

<a
  href="#"
  {...hoverCard.trigger}
  onclick={(e) => e.preventDefault()}
  onmouseenter={open}
  onmouseleave={scheduleClose}
  onfocusin={open}
  onfocusout={scheduleClose}
  class={cn("text-sm font-medium underline underline-offset-4 hover:text-primary", className)}
>
  {triggerLabel}
</a>
<div
  {...hoverCard.content}
  onmouseenter={cancelClose}
  onmouseleave={scheduleClose}
  class="z-50 w-72 rounded-md border border-border bg-popover p-4 text-popover-foreground shadow-md"
>
  {#if preview}
    {@render preview()}
  {:else}
    <p class="text-sm text-muted-foreground">{t("demo_hover_card_empty")}</p>
  {/if}
</div>
