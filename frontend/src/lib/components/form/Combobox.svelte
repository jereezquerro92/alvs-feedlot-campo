<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Searchable single-select on the melt/builders Combobox ([[MELT-UI]]) — the
  builder owns the text input, highlight, and floating placement; filtering
  the option list by `inputValue` is the caller's list, done here inline.
-->
<script lang="ts" module>
  export type ComboboxOption = {
    value: string;
    label: string;
  };
</script>

<script lang="ts">
  import { Combobox } from "melt/builders";
  import { cn } from "$lib/utils";

  let {
    options = [],
    value = $bindable(undefined),
    label = "",
    placeholder = "",
    emptyText = "",
    disabled = false,
    class: className = undefined,
  }: {
    options?: ComboboxOption[];
    value?: string | undefined;
    /** Accessible label, i18n-supplied by the caller. */
    label?: string;
    placeholder?: string;
    /** Shown when the current query matches nothing. */
    emptyText?: string;
    disabled?: boolean;
    class?: string;
  } = $props();

  const combobox = new Combobox<string>({
    value: () => value,
    onValueChange: (v) => (value = v),
  });

  const filtered = $derived(
    options.filter((o) => o.label.toLowerCase().includes(combobox.inputValue.toLowerCase())),
  );
</script>

<div class={cn("flex flex-col gap-1.5", className)}>
  <label {...combobox.label} class="sr-only">{label}</label>
  <input
    {...combobox.input}
    {placeholder}
    {disabled}
    class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-base shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm"
  />
  <div
    {...combobox.content}
    class="z-50 max-h-64 overflow-y-auto rounded-md border bg-popover p-1 text-popover-foreground shadow-md"
  >
    {#if filtered.length === 0}
      <p class="px-2 py-1.5 text-sm text-muted-foreground">{emptyText}</p>
    {:else}
      {#each filtered as option (option.value)}
        {@const item = combobox.getOption(option.value, option.label)}
        <div
          {...item}
          class={cn(
            "flex cursor-pointer items-center justify-between gap-2 rounded-sm px-2 py-1.5 text-sm",
            item["data-highlighted"] !== undefined && "bg-accent text-accent-foreground",
          )}
        >
          {option.label}
          {#if combobox.isSelected(option.value)}
            <span aria-hidden="true">✓</span>
          {/if}
        </div>
      {/each}
    {/if}
  </div>
</div>
