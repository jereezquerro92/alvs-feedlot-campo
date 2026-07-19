<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Persistent, viewport-docked collapsible drawer with a peek tab ([[MELT-UI]]:
  no Melt builder needed — this is layout state, not a float/dismiss overlay
  like overlay/Popover). The drawer stays mounted and slides its whole width
  off-screen, leaving only the tab at the viewport edge. `side` docks it left
  or right; `open` is bindable so a shell can drive it. Toggling is local
  layout state only — no mutating action on the default invocation (adr-22 r2);
  a zero-prop call renders a collapsed, self-labeled drawer and never throws
  (adr-22 r1).
-->
<script lang="ts">
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";
  import type { Snippet } from "svelte";

  let {
    open = $bindable(false),
    side = "left",
    title = t("drawer_default_title"),
    width = "18rem",
    openLabel = t("drawer_open"),
    closeLabel = t("drawer_close"),
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
    children?: Snippet;
    class?: string;
  } = $props();

  const isLeft = $derived(side === "left");
  // Collapsed → translate the whole panel off its own edge; the tab, anchored
  // just outside the body, lands flush at the viewport edge (matches the
  // reference peek-tab behavior).
  const offClass = $derived(isLeft ? "-translate-x-full" : "translate-x-full");
  // Chevron points the direction the tab will move the drawer.
  const glyph = $derived(isLeft ? (open ? "‹" : "›") : open ? "›" : "‹");
</script>

<aside
  class={cn(
    "fixed inset-y-0 z-40 flex transition-transform duration-300 ease-out motion-reduce:transition-none",
    isLeft ? "left-0" : "right-0",
    !open && offClass,
    className,
  )}
  style={`width: ${width}`}
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
    onclick={() => (open = !open)}
    aria-label={open ? closeLabel : openLabel}
    aria-expanded={open}
    class={cn(
      "absolute top-1/2 flex h-12 w-7 -translate-y-1/2 items-center justify-center bg-background text-muted-foreground shadow-md transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
      isLeft
        ? "left-full rounded-r-md border border-l-0 border-border"
        : "right-full rounded-l-md border border-r-0 border-border",
    )}
  >
    <span aria-hidden="true">{glyph}</span>
  </button>
</aside>
