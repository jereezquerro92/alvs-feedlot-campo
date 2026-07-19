<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Single-date filter on the melt/builders Popover ([[MELT-UI]]) — Melt 0.44
  ships no Date Picker builder, so the calendar itself is the platform's
  native <input type="date">; Popover supplies the anchored, focus-trapped
  surface around it. Value is a plain ISO "YYYY-MM-DD" string — no
  @internationalized/date dependency.
-->
<script lang="ts">
  import { Popover } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";

  let {
    value = $bindable(undefined),
    label,
    placeholder = "",
    clearLabel = "",
    min = undefined,
    max = undefined,
    class: className = undefined,
  }: {
    value?: string | undefined;
    /** Accessible label, i18n-supplied by the caller. */
    label: string;
    placeholder?: string;
    /** Shown next to a chosen value; omit to hide the clear affordance. */
    clearLabel?: string;
    min?: string;
    max?: string;
    class?: string;
  } = $props();

  const popover = new Popover();

  const formatted = $derived(
    value
      ? new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { dateStyle: "medium" })
      : undefined,
  );
</script>

<div class={cn("flex flex-col gap-1.5", className)}>
  <Button
    type="button"
    variant="outline"
    {...popover.trigger}
    aria-label={label}
    class="w-full justify-between font-normal"
  >
    <span class={cn("truncate", !formatted && "text-muted-foreground")}>
      {formatted ?? placeholder}
    </span>
    <span aria-hidden="true" class={cn("shrink-0 transition-transform", popover.open && "rotate-180")}>⌄</span>
  </Button>
  <div
    {...popover.content}
    class="z-50 rounded-md border bg-popover p-2 text-popover-foreground shadow-md"
  >
    <div class="flex items-center gap-2">
      <input
        type="date"
        bind:value
        {min}
        {max}
        aria-label={label}
        class="h-9 rounded-md border border-input bg-background px-2 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      />
      {#if value && clearLabel}
        <Button type="button" variant="ghost" size="sm" onclick={() => (value = undefined)}>
          {clearLabel}
        </Button>
      {/if}
    </div>
  </div>
</div>
