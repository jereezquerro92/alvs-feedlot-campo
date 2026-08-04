<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[COMPONENTIZATION]]
     LIVE-DOC:END -->

<!-- Nothing pending is nothing shown: a nav badge has no column to hold open. -->
<script lang="ts">
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  let {
    count = 0,
    class: className = undefined,
    ...rest
  }: {
    count?: number;
    class?: string;
    [key: string]: unknown;
  } = $props();

  const shown = $derived(Number.isFinite(count) && count > 0);
</script>

{#if shown}
  <span
    class={cn(
      "ml-auto inline-flex min-w-[1.5rem] items-center justify-center rounded-full bg-primary px-1.5 py-0.5 text-xs font-semibold text-primary-foreground",
      className,
    )}
    aria-label={`${count} ${t("shell_nav_badge_pending")}`}
    {...rest}>{count}</span
  >
{/if}
