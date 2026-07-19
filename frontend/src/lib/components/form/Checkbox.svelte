<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Boolean checkbox on the melt/builders Toggle ([[MELT-UI]]) — melt 0.44 ships
  no dedicated Checkbox builder, so this follows the same Toggle-as-boolean
  pattern as ThemeModeToggle, with role="checkbox" laid over the builder's
  toggle-button semantics.
-->
<script lang="ts">
  import { Toggle } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";

  let {
    checked = $bindable(false),
    label = undefined,
    disabled = false,
    name = undefined,
    class: className = undefined,
  }: {
    checked?: boolean;
    label?: string;
    disabled?: boolean;
    /** When set, a hidden input mirrors `checked` for plain form submission. */
    name?: string;
    class?: string;
  } = $props();

  const toggle = new Toggle({
    value: () => checked,
    onValueChange: (v) => (checked = v),
    disabled: () => disabled,
  });
</script>

<label
  class={cn(
    "inline-flex items-center gap-2 text-sm",
    disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer",
    className,
  )}
>
  <Button
    variant="bare"
    {...toggle.trigger}
    role="checkbox"
    aria-checked={toggle.value}
    class={cn(
      "flex h-4 w-4 shrink-0 items-center justify-center rounded-sm border border-input shadow-sm",
      toggle.value ? "border-primary bg-primary text-primary-foreground" : "bg-background",
    )}
  >
    {#if toggle.value}
      <span aria-hidden="true" class="text-[0.65rem] leading-none">✓</span>
    {/if}
  </Button>
  {#if label}<span>{label}</span>{/if}
  {#if name}<input {...toggle.hiddenInput} {name} />{/if}
</label>
