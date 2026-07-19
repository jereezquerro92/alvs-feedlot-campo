<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  From/to date-range filter on the melt/builders Popover ([[MELT-UI]]) — same
  native-<input type="date"> rationale as form/DatePicker; two independently
  bindable ISO "YYYY-MM-DD" strings, each constraining the other's range.
-->
<script lang="ts">
  import { Popover } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";

  let {
    from = $bindable(undefined),
    to = $bindable(undefined),
    label,
    fromLabel,
    toLabel,
    placeholder = "",
    clearLabel = "",
    min = undefined,
    max = undefined,
    class: className = undefined,
  }: {
    from?: string | undefined;
    to?: string | undefined;
    /** Accessible label for the trigger, i18n-supplied by the caller. */
    label: string;
    /** Accessible label for the "from" input. */
    fromLabel: string;
    /** Accessible label for the "to" input. */
    toLabel: string;
    placeholder?: string;
    /** Shown next to a chosen range; omit to hide the clear affordance. */
    clearLabel?: string;
    min?: string;
    max?: string;
    class?: string;
  } = $props();

  const popover = new Popover();

  const format = (iso: string) =>
    new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { dateStyle: "medium" });
  const formatted = $derived(
    from && to ? `${format(from)} – ${format(to)}` : from ? format(from) : to ? format(to) : undefined,
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
    class="z-50 rounded-md border bg-popover p-3 text-popover-foreground shadow-md"
  >
    <div class="flex flex-col gap-2">
      <div class="flex items-center gap-2">
        <input
          type="date"
          bind:value={from}
          {min}
          max={to ?? max}
          aria-label={fromLabel}
          class="h-9 rounded-md border border-input bg-background px-2 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />
        <span aria-hidden="true" class="text-muted-foreground">–</span>
        <input
          type="date"
          bind:value={to}
          min={from ?? min}
          {max}
          aria-label={toLabel}
          class="h-9 rounded-md border border-input bg-background px-2 text-sm text-foreground shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />
      </div>
      {#if (from || to) && clearLabel}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          class="self-start"
          onclick={() => {
            from = undefined;
            to = undefined;
          }}
        >
          {clearLabel}
        </Button>
      {/if}
    </div>
  </div>
</div>
