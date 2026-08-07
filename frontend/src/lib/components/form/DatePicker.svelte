<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Single-date control: Melt Popover trigger + form/Calendar grid ([[MELT-UI]]).
  Value is a plain ISO "YYYY-MM-DD" string — no @internationalized/date.
  Mounts with zero props-safe defaults via Calendar (adr-22 r1/r2).
-->
<script lang="ts">
  import { Popover } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import Calendar from "./Calendar.svelte";
  import { cn } from "$lib/utils";

  let {
    value = $bindable(undefined),
    label = "",
    placeholder = "",
    clearLabel = "",
    min = undefined,
    max = undefined,
    disabled = false,
    id = undefined,
    class: className = undefined,
  }: {
    value?: string | undefined;
    /** Accessible label, i18n-supplied by the caller. */
    label?: string;
    placeholder?: string;
    /** Shown next to a chosen value; omit to hide the clear affordance. */
    clearLabel?: string;
    min?: string;
    max?: string;
    disabled?: boolean;
    id?: string;
    class?: string;
  } = $props();

  const popover = new Popover();

  const formatted = $derived.by(() => {
    if (!value) return undefined;
    const d = new Date(`${value}T00:00:00`);
    if (Number.isNaN(d.getTime())) return undefined;
    return d.toLocaleDateString(undefined, { dateStyle: "medium" });
  });

  function onPick(next: string): void {
    value = next;
    popover.open = false;
  }
</script>

<div class={cn("flex flex-col gap-1.5", className)}>
  <Button
    type="button"
    variant="outline"
    {id}
    {disabled}
    {...popover.trigger}
    aria-label={label}
    class="w-full justify-start gap-2 font-normal"
  >
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.75"
      stroke-linecap="round"
      stroke-linejoin="round"
      class="size-4 shrink-0 text-muted-foreground"
      aria-hidden="true"
    >
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <path d="M16 2v4M8 2v4M3 10h18" />
    </svg>
    <span class={cn("min-w-0 flex-1 truncate text-left", !formatted && "text-muted-foreground")}>
      {formatted ?? placeholder}
    </span>
    <span aria-hidden="true" class={cn("shrink-0 text-muted-foreground transition-transform", popover.open && "rotate-180")}>⌄</span>
  </Button>
  <div
    {...popover.content}
    class="z-50 rounded-md border bg-popover p-2 text-popover-foreground shadow-md"
  >
    <Calendar bind:value {min} {max} onValueChange={onPick} />
    {#if value && clearLabel}
      <div class="mt-2 flex justify-end">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          {disabled}
          onclick={() => {
            value = undefined;
          }}
        >
          {clearLabel}
        </Button>
      </div>
    {/if}
  </div>
</div>
