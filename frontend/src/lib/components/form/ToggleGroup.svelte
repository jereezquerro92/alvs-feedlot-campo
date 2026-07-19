<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Single-select segmented group composed of Melt Toggle builder instances
  ([[MELT-UI]]) — melt 0.44 ships no dedicated ToggleGroup builder, so this is
  a composition of the real Melt Toggle (one instance per option, mutually
  exclusive by construction), not a hand-rolled-from-scratch fallback, the
  same absence-with-composition shape as PinInput's siblings above it in this
  folder. options/value default to a small demo option set with the first
  entry selected and onValueChange defaults to a no-op, so a zero-prop
  invocation renders a sensible default and never mutates anything on its
  own (adr-22 r1/r2).
-->
<script lang="ts">
  import { Toggle } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  export type ToggleGroupOption = { value: string; label: string };

  const defaultOptions: ToggleGroupOption[] = [
    { value: "list", label: t("demo_toggle_group_option_list") },
    { value: "grid", label: t("demo_toggle_group_option_grid") },
  ];

  let {
    options = defaultOptions,
    value = $bindable(options[0]?.value ?? ""),
    onValueChange = () => {},
    disabled = false,
    label = undefined,
    class: className = undefined,
  }: {
    options?: ToggleGroupOption[];
    value?: string;
    onValueChange?: (value: string) => void;
    disabled?: boolean;
    label?: string;
    class?: string;
  } = $props();

  const toggles = $derived(
    options.map(
      (opt) =>
        new Toggle({
          value: () => value === opt.value,
          onValueChange: (v) => {
            if (v) {
              value = opt.value;
              onValueChange(opt.value);
            }
          },
          disabled: () => disabled,
        }),
    ),
  );
</script>

<div
  role="group"
  aria-label={label ?? t("demo_toggle_group_label")}
  class={cn("inline-flex gap-1 rounded-md border border-border bg-muted p-1", className)}
>
  {#each options as opt, i (opt.value)}
    <Button
      type="button"
      variant="bare"
      {...toggles[i].trigger}
      class={cn(
        "rounded px-3 py-1 text-sm transition-colors",
        toggles[i].value ? "bg-primary text-primary-foreground" : "text-muted-foreground",
        disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer",
      )}
    >
      {opt.label}
    </Button>
  {/each}
</div>
