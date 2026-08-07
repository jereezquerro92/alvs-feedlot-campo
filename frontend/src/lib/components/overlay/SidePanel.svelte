<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Persistent, viewport-docked collapsible panel with a peek tab ([[MELT-UI]]:
  no Melt builder — layout state, not a float/dismiss overlay). Distinct from
  Drawer (full-height edge panel used by ChatDrawer) and FancyDrawer (floating
  sibling): SidePanel is the generic app-shell rail / context-detail panel.
  Slides its full width off-screen, leaving only the peek tab. Zero-prop safe
  (adr-22 r1); toggling is local layout state only (adr-22 r2).
-->
<script lang="ts">
  import { onDestroy } from "svelte";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";
  import type { Snippet } from "svelte";

  const CLOSE_DELAY_MS = 2000;

  let {
    open = $bindable(false),
    side = "left",
    title = t("side_panel_default_title"),
    width = "18rem",
    openLabel = t("side_panel_open"),
    closeLabel = t("side_panel_close"),
    children,
    class: className = undefined,
  }: {
    open?: boolean;
    side?: "left" | "right";
    title?: string;
    width?: string;
    openLabel?: string;
    closeLabel?: string;
    children?: Snippet;
    class?: string;
  } = $props();

  const isLeft = $derived(side === "left");
  const offClass = $derived(isLeft ? "-translate-x-full" : "translate-x-full");
  const glyph = $derived(isLeft ? (open ? "‹" : "›") : open ? "›" : "‹");

  let rootEl: HTMLElement | undefined = $state();
  let closeTimer: ReturnType<typeof setTimeout> | undefined;
  let suppressHoverOpen = $state(false);

  function cancelClose() {
    clearTimeout(closeTimer);
    closeTimer = undefined;
  }

  function scheduleClose() {
    cancelClose();
    closeTimer = setTimeout(() => {
      open = false;
    }, CLOSE_DELAY_MS);
  }

  function onPanelPointerEnter(event: PointerEvent) {
    if (event.pointerType !== "mouse") return;
    cancelClose();
    if (!suppressHoverOpen) {
      open = true;
    }
  }

  function onPanelPointerLeave(event: PointerEvent) {
    if (event.pointerType !== "mouse") return;
    suppressHoverOpen = false;
    if (open) {
      scheduleClose();
    }
  }

  function onTabClick() {
    cancelClose();
    if (open) {
      open = false;
      suppressHoverOpen = true;
    } else {
      open = true;
      suppressHoverOpen = false;
    }
  }

  function onDocumentPointerDown(event: PointerEvent) {
    if (!open || !rootEl) return;
    const target = event.target;
    if (target instanceof Node && rootEl.contains(target)) return;
    cancelClose();
    open = false;
    suppressHoverOpen = false;
  }

  $effect(() => {
    if (!open) {
      cancelClose();
      return;
    }
    document.addEventListener("pointerdown", onDocumentPointerDown, true);
    return () => {
      document.removeEventListener("pointerdown", onDocumentPointerDown, true);
    };
  });

  onDestroy(cancelClose);
</script>

<aside
  bind:this={rootEl}
  onpointerenter={onPanelPointerEnter}
  onpointerleave={onPanelPointerLeave}
  class={cn("fixed inset-y-0 z-40", isLeft ? "left-0" : "right-0", className)}
  style={`width: ${width}`}
>
  <div
    class={cn(
      "relative flex h-full w-full transition-transform duration-300 ease-out motion-reduce:transition-none",
      !open && offClass,
    )}
  >
    <div
      inert={!open}
      aria-hidden={!open}
      class={cn(
        "flex min-w-0 flex-1 flex-col overflow-y-auto bg-background shadow-xl",
        isLeft ? "border-r border-border" : "border-l border-border",
      )}
    >
      <div class="flex items-center border-b border-border px-4 py-3">
        <h2 class="truncate text-sm font-semibold text-foreground">{title}</h2>
      </div>
      <div class="flex-1 p-4 text-sm text-muted-foreground">
        {#if children}
          {@render children()}
        {:else}
          <p>{t("side_panel_empty")}</p>
        {/if}
      </div>
    </div>

    <button
      type="button"
      onclick={onTabClick}
      aria-label={open ? closeLabel : openLabel}
      aria-expanded={open}
      class={cn(
        "absolute top-1/2 flex h-12 w-7 -translate-y-1/2 items-center justify-center bg-background text-muted-foreground shadow-md transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
        isLeft
          ? "left-full rounded-r-2xl border border-l-0 border-border"
          : "right-full rounded-l-2xl border border-r-0 border-border",
      )}
    >
      <span aria-hidden="true">{glyph}</span>
    </button>
  </div>
</aside>
