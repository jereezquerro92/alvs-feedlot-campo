<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[COMPONENTIZATION]]
     LIVE-DOC:END -->

<!--
  Pin control for FancyNav: open lock = floating drawer; closed lock = docked
  rail. Primary fill + primary-foreground label. Zero-prop safe (adr-22 r1).
-->
<script lang="ts">
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  let {
    locked = false,
    label = t("shell_nav_label"),
    class: className = undefined,
    onclick,
  }: {
    locked?: boolean;
    label?: string;
    class?: string;
    onclick?: (event: MouseEvent) => void;
  } = $props();

  const aria = $derived(
    locked ? t("shell_nav_unlock_aria") : t("shell_nav_lock_aria"),
  );
</script>

<button
  type="button"
  {onclick}
  aria-pressed={locked}
  aria-label={aria}
  class={cn(
    "flex w-full items-center gap-2 rounded-lg bg-primary px-2.5 py-1.5 text-xs font-semibold tracking-wide text-primary-foreground shadow-sm transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
    className,
  )}
>
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="size-3.5 shrink-0"
    aria-hidden="true"
  >
    {#if locked}
      <!-- Closed lock -->
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    {:else}
      <!-- Open lock — shackle swung open -->
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 7.5-1.8" />
    {/if}
  </svg>
  <span class="truncate">{label}</span>
</button>
