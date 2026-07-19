<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Exploratory spike (issue #255): a small triangle fixed at the viewport's
  top-left corner, holding a home icon. Zero props renders a safe, inert
  default and never throws (adr-22 r1); "go home" fires ONLY through the
  caller-supplied `href` (rung-1 plain anchor) or `onHome` callback — never
  an implicit default navigation (adr-22 r2). Fill tracks the H1 color token
  (`bg-primary`) and the icon uses its paired `--primary-foreground` token,
  both per-theme, no hardcoded OKLCH/hex ([[DESIGN-SYSTEM]]). Fixed-position
  ownership follows the overlay/Drawer precedent (component owns its own
  anchor, not composed inline by a page). An interactive branch (`href` or
  `onHome` supplied) never renders with an empty accessible name (issue
  #283, WCAG 4.1.2): the caller's `ariaLabel` wins when given, otherwise the
  component self-resolves the existing `home_triangle_aria_label` i18n key
  as a non-empty fallback — resolving an i18n KEY in-component is not the
  hardcoded-string LOCALIZATION violates (adr-01).
-->
<script lang="ts">
  import { cn } from "$lib/utils";
  import { resolveHomeTarget, resolveAccessibleLabel } from "$lib/home-triangle";
  import { t } from "../../../i18n";

  let {
    href = undefined,
    onHome = undefined,
    ariaLabel = undefined,
    class: className = undefined,
  }: {
    /** Rung-1 plain-anchor home navigation; preferred shape. */
    href?: string;
    /** Escalation point for a future richer "go home" behavior. */
    onHome?: () => void;
    /** Caller-supplied accessible name (LOCALIZATION); falls back to an i18n default when the target is interactive and this is omitted. */
    ariaLabel?: string;
    class?: string;
  } = $props();

  const target = $derived(resolveHomeTarget(href, onHome));
  const resolvedAriaLabel = $derived(
    resolveAccessibleLabel(target, ariaLabel, t("home_triangle_aria_label")),
  );
</script>

{#snippet icon()}
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="h-3.5 w-3.5"
    aria-hidden="true"
  >
    <path d="M3 11.5 12 4l9 7.5" />
    <path d="M5.5 10v9a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-9" />
  </svg>
{/snippet}

{#snippet shape()}
  <span
    class={cn(
      "flex h-9 w-9 items-start justify-start bg-primary text-primary-foreground",
      "[clip-path:polygon(0_0,100%_0,0_100%)]",
      className,
    )}
  >
    <span class="pl-1 pt-1">
      {@render icon()}
    </span>
  </span>
{/snippet}

{#if target.kind === "link"}
  <a href={target.href} aria-label={resolvedAriaLabel} class="fixed left-0 top-0 z-50">
    {@render shape()}
  </a>
{:else if target.kind === "action"}
  <button type="button" onclick={target.onHome} aria-label={resolvedAriaLabel} class="fixed left-0 top-0 z-50">
    {@render shape()}
  </button>
{:else}
  <span aria-hidden="true" class="fixed left-0 top-0 z-50">
    {@render shape()}
  </span>
{/if}
