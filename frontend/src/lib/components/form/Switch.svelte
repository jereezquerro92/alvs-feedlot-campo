<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Boolean switch on the melt/builders Toggle ([[MELT-UI]]) — same builder as
  Checkbox and ThemeModeToggle, styled as a pill/thumb and layered with
  role="switch" for correct semantics over the builder's toggle-button base.
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
    role="switch"
    aria-checked={toggle.value}
    class={cn(
      "relative inline-flex h-5 w-9 shrink-0 items-center rounded-full border border-input transition-colors",
      toggle.value ? "bg-primary" : "bg-input",
    )}
  >
    <span
      aria-hidden="true"
      class={cn(
        "inline-block h-3.5 w-3.5 translate-x-0.5 rounded-full bg-background shadow transition-transform",
        toggle.value && "translate-x-4",
      )}
    ></span>
  </Button>
  {#if label}<span>{label}</span>{/if}
  {#if name}<input {...toggle.hiddenInput} {name} />{/if}
</label>
