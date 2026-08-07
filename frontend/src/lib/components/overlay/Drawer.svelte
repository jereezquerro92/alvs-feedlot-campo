<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Persistent, viewport-docked collapsible drawer with a peek tab ([[MELT-UI]]:
  no Melt builder needed — this is layout state, not a float/dismiss overlay
  like overlay/Popover). The drawer stays mounted and slides its whole width
  off-screen, leaving only the tab at the viewport edge. `side` docks it left
  or right; `open` is bindable so a shell can drive it. Interaction is always
  the same on either side: hover the tab (mouse) to open; leave the drawer to
  close after a 2s cooldown; click outside or click the tab caret to close
  immediately; click the caret when closed to open. Hover-open is mouse-only so
  a touch tap toggles once instead of open-then-close. A zero-prop call renders
  a collapsed, self-labeled drawer and never throws (adr-22 r1); toggling is
  local layout state only — no mutating action on the default invocation
  (adr-22 r2).

  Shell stacking: same ClientRouter VT contract as FancyDrawer — `viewTransitionName`
  (ChatDrawer: `shell-chat`) on the outer fixed <aside> with NO transform;
  open/close translate lives on the inner track so VT capture stays solid.
-->
<script lang="ts">
  import { onDestroy } from "svelte";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";
  import type { Snippet } from "svelte";

  /** Pointer-leave → close cooldown; always in force for this component. */
  const CLOSE_DELAY_MS = 2000;

  let {
    open = $bindable(false),
    side = "left",
    title = t("drawer_default_title"),
    width = "18rem",
    openLabel = t("drawer_open"),
    closeLabel = t("drawer_close"),
    /** Optional fixed peek-tab glyph (e.g. "?" for help). When omitted, a
     * directional chevron follows open/side. */
    tabGlyph = "",
    /**
     * CSS `view-transition-name` for shell chrome. Empty keeps showcase /
     * demos out of the VT layer; ChatDrawer passes `shell-chat`.
     */
    viewTransitionName = "",
    children,
    class: className = undefined,
  }: {
    open?: boolean;
    side?: "left" | "right";
    title?: string;
    /** CSS width of the drawer body; the tab stays outside it. */
    width?: string;
    /** Accessible label for the tab when collapsed, i18n-supplied by the caller. */
    openLabel?: string;
    /** Accessible label for the tab when expanded. */
    closeLabel?: string;
    tabGlyph?: string;
    viewTransitionName?: string;
    children?: Snippet;
    class?: string;
  } = $props();

  const shellName = $derived(viewTransitionName.trim());

  /** Outer shell: width + optional VT name. No transform. */
  const outerStyle = $derived(
    [`width: ${width}`, shellName ? `view-transition-name: ${shellName}` : ""]
      .filter(Boolean)
      .join("; "),
  );

  const isLeft = $derived(side === "left");
  // Collapsed → translate the INNER track off its own edge; the tab, anchored
  // just outside the body, lands flush at the viewport edge.
  const offClass = $derived(isLeft ? "-translate-x-full" : "translate-x-full");
  const glyph = $derived(
    tabGlyph || (isLeft ? (open ? "‹" : "›") : open ? "›" : "‹"),
  );

  let rootEl: HTMLElement | undefined = $state();
  let closeTimer: ReturnType<typeof setTimeout> | undefined;
  /** After a caret-close while the pointer is still on the tab, ignore hover-open until leave. */
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
    // Touch/pen activate via the caret click only — synthesized mouseenter after
    // a tap would otherwise open-then-close in one gesture.
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
  class={cn("fixed inset-y-0 z-40", isLeft ? "left-0" : "right-0", className)}
  style={outerStyle}
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
          <p>{t("drawer_empty")}</p>
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
