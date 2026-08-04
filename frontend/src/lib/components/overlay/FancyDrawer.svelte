<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[COMPONENTIZATION]]
     LIVE-DOC:END -->

<!--
  FancyDrawer — sibling of overlay/Drawer with a content-sized floating
  silhouette. Same interaction contract (hover-open, 2s leave cooldown,
  outside/caret dismiss). Title strip is optional: empty `title` hides
  shell/NavPanelTitle (feedlot FancyNav); showcase still passes titles.
  Geometry: default width ⅔ of Drawer's 18rem (12rem), height hugs content
  (vertically centered), exposed-side rounding only. Zero-prop safe (adr-22 r1).
-->
<script lang="ts">
  import { onDestroy } from "svelte";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";
  import type { Snippet } from "svelte";
  import NavPanelTitle from "$lib/components/shell/NavPanelTitle.svelte";

  /** Pointer-leave → close cooldown; same as overlay/Drawer. */
  const CLOSE_DELAY_MS = 2000;

  /** ⅔ of Drawer's default `18rem` width. */
  const DEFAULT_WIDTH = "12rem";

  let {
    open = $bindable(false),
    side = "left",
    /** Empty string hides the panel title strip (feedlot FancyNav). */
    title = t("fancy_drawer_default_title"),
    width = DEFAULT_WIDTH,
    openLabel = t("fancy_drawer_open"),
    closeLabel = t("fancy_drawer_close"),
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

  const showTitle = $derived(title.trim().length > 0);

  const isLeft = $derived(side === "left");
  // Keep -translate-y-1/2 always (viewport vertical center); slide off on X when closed.
  const slideClass = $derived(
    open
      ? "-translate-y-1/2"
      : isLeft
        ? "-translate-x-full -translate-y-1/2"
        : "translate-x-full -translate-y-1/2",
  );
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

  function onDrawerPointerEnter(event: PointerEvent) {
    if (event.pointerType !== "mouse") return;
    cancelClose();
    if (!suppressHoverOpen) {
      open = true;
    }
  }

  function onDrawerPointerLeave(event: PointerEvent) {
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
  onpointerenter={onDrawerPointerEnter}
  onpointerleave={onDrawerPointerLeave}
  class={cn(
    "fixed top-1/2 z-40 flex h-fit max-h-[calc(100vh-3rem)] transition-transform duration-300 ease-out motion-reduce:transition-none",
    isLeft ? "left-0" : "right-0",
    slideClass,
    className,
  )}
  style={`width: ${width}`}
>
  <div
    inert={!open}
    aria-hidden={!open}
    class={cn(
      "flex min-w-0 flex-1 flex-col overflow-y-auto bg-background shadow-xl",
      isLeft
        ? "rounded-r-2xl border border-l-0 border-border"
        : "rounded-l-2xl border border-r-0 border-border",
    )}
  >
    <div class="flex flex-col gap-0 px-3 py-4">
      {#if showTitle}
        <NavPanelTitle {title} />
      {/if}
      <div class={cn("text-sm text-muted-foreground", showTitle && "pt-4")}>
        {#if children}
          {@render children()}
        {:else}
          <p>{t("fancy_drawer_empty")}</p>
        {/if}
      </div>
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
</aside>
