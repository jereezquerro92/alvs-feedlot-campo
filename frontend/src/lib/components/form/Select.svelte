<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Single-select popover on the melt/builders Select ([[MELT-UI]]) — the
  builder owns roving highlight, aria-expanded/aria-selected, and floating
  placement; this component is the styled shell.
-->
<script lang="ts" module>
  export type SelectOption = {
    value: string;
    label: string;
    disabled?: boolean;
  };
</script>

<script lang="ts">
  import { Select } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";

  let {
    options = [],
    value = $bindable(undefined),
    label = "",
    placeholder = "",
    disabled = false,
    class: className = undefined,
  }: {
    options?: SelectOption[];
    value?: string | undefined;
    /** Accessible label, i18n-supplied by the caller. */
    label?: string;
    placeholder?: string;
    disabled?: boolean;
    class?: string;
  } = $props();

  const select = new Select<string>({
    value: () => value,
    onValueChange: (v) => (value = v),
    disabled: () => disabled,
  });

  const selectedLabel = $derived(options.find((o) => o.value === value)?.label);
</script>

<div class={cn("flex flex-col gap-1.5", className)}>
  <label {...select.label} class="sr-only">{label}</label>
  <Button
    type="button"
    variant="outline"
    {...select.trigger}
    class="w-full justify-between font-normal"
  >
    <span class={cn("truncate", !selectedLabel && "text-muted-foreground")}>
      {selectedLabel ?? placeholder}
    </span>
    <span aria-hidden="true" class={cn("shrink-0 transition-transform", select.open && "rotate-180")}>⌄</span>
  </Button>
  <div
    {...select.content}
    class="z-50 max-h-64 overflow-y-auto rounded-md border bg-popover p-1 text-popover-foreground shadow-md"
  >
    {#each options as option (option.value)}
      {@const item = select.getOption(option.value, option.label)}
      <div
        {...item}
        aria-disabled={option.disabled}
        class={cn(
          "flex cursor-pointer items-center justify-between gap-2 rounded-sm px-2 py-1.5 text-sm",
          item["data-highlighted"] !== undefined && "bg-accent text-accent-foreground",
          option.disabled && "pointer-events-none opacity-50",
        )}
      >
        {option.label}
        {#if select.isSelected(option.value)}
          <span aria-hidden="true">✓</span>
        {/if}
      </div>
    {/each}
  </div>
</div>
