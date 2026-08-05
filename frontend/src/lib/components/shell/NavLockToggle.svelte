<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Pin control for FancyNav: open lock = floating drawer; closed lock = docked
  rail. Icon-only disc (same size + tokens as Breadcrumb home) — lives in the
  FancyNav footer with profile + theme. Zero-prop safe (adr-22 r1).
-->
<script lang="ts">
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  let {
    locked = false,
    class: className = undefined,
    onclick,
  }: {
    locked?: boolean;
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
  title={aria}
  class={cn(
    "inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-foreground text-background transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
    className,
  )}
>
  <svg viewBox="0 0 24 24" fill="currentColor" class="size-4" aria-hidden="true">
    {#if locked}
      <path
        d="M17 10V8A5 5 0 0 0 7 8v2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-1Zm-8 0V8a3 3 0 1 1 6 0v2H9Zm3 5.5a1.5 1.5 0 0 1 .75 2.8V20h-1.5v-1.7a1.5 1.5 0 0 1 .75-2.8Z"
      />
    {:else}
      <path
        d="M17 10h1a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h7V8a3 3 0 0 0-5.76-1.2l-1.5-.8A5 5 0 0 1 16 8v2Zm-5 5.5a1.5 1.5 0 0 0-.75 2.8V20h1.5v-1.7a1.5 1.5 0 0 0-.75-2.8Z"
      />
    {/if}
  </svg>
</button>
