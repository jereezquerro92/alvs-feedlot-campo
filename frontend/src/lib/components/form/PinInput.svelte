<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Numeric confirmation-code field on the melt/builders PinInput ([[MELT-UI]]) —
  melt 0.44 ships a dedicated PinInput builder, so unlike Pagination/Dropdown
  Menu above this is a direct wrap, not a hand-rolled fallback. length/onComplete
  default to a safe 6-digit empty state and a no-op callback so a zero-prop
  invocation renders without throwing and fires no mutating call (adr-22 r1/r2).
-->
<script lang="ts">
  import { PinInput as MeltPinInput } from "melt/builders";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  let {
    value = $bindable(""),
    length = 6,
    onComplete = () => {},
    disabled = false,
    label = undefined,
    name = undefined,
    class: className = undefined,
  }: {
    value?: string;
    length?: number;
    onComplete?: (value: string) => void;
    disabled?: boolean;
    label?: string;
    name?: string;
    class?: string;
  } = $props();

  const pin = new MeltPinInput({
    value: () => value,
    onValueChange: (v) => (value = v),
    onComplete,
    maxLength: () => length,
    disabled: () => disabled,
    type: "numeric",
  });
</script>

<div class={cn("flex flex-col gap-2", className)}>
  {#if label}<span class="text-sm text-muted-foreground">{label}</span>{/if}
  <div {...pin.root} aria-label={t("demo_pin_input_group")} class="flex gap-2">
    {#each pin.inputs as inputProps, i (i)}
      <input
        {...inputProps}
        class={cn(
          "h-11 w-9 rounded-md border border-border bg-popover text-center text-lg text-popover-foreground shadow-sm outline-none",
          "focus-visible:border-primary",
          inputProps["data-filled"] !== undefined && "border-primary bg-primary text-primary-foreground",
          disabled && "cursor-not-allowed opacity-50",
        )}
      />
    {/each}
  </div>
  {#if name}<input type="hidden" {name} {value} />{/if}
</div>
