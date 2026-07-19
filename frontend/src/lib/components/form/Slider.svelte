<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Numeric range control on the melt/builders Slider ([[MELT-UI]]) — a direct
  wrap, not a hand-rolled fallback. min/max/step/value all default to a
  sensible mid-range state and onValueChange defaults to a no-op, so a
  zero-prop invocation renders and drags without throwing or mutating
  anything (adr-22 r1/r2). The filled range and thumb are drawn from
  `slider.value` directly rather than the builder's `--percentage` CSS var,
  since Tailwind utility classes cannot read a computed custom property.
-->
<script lang="ts">
  import { Slider as MeltSlider } from "melt/builders";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  let {
    value = $bindable(50),
    min = 0,
    max = 100,
    step = 1,
    onValueChange = () => {},
    disabled = false,
    label = undefined,
    name = undefined,
    class: className = undefined,
  }: {
    value?: number;
    min?: number;
    max?: number;
    step?: number;
    onValueChange?: (value: number) => void;
    disabled?: boolean;
    label?: string;
    name?: string;
    class?: string;
  } = $props();

  const slider = new MeltSlider({
    value: () => value,
    min: () => min,
    max: () => max,
    step: () => step,
    onValueChange: (v) => {
      value = v;
      onValueChange(v);
    },
  });

  const percentage = $derived(((slider.value - min) / (max - min || 1)) * 100);
</script>

<div class={cn("flex flex-col gap-2", className)}>
  {#if label}<span class="text-sm text-muted-foreground">{label}</span>{/if}
  <div
    {...slider.root}
    aria-label={label ?? t("demo_slider_label")}
    class={cn("relative flex h-5 w-full items-center", disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer")}
  >
    <div class="absolute inset-x-0 h-1.5 rounded-full bg-muted"></div>
    <div class="absolute h-1.5 rounded-full bg-primary" style={`width: ${percentage}%`}></div>
    <span
      {...slider.thumb}
      class="absolute h-4 w-4 rounded-full border border-border bg-primary"
      style={`left: ${percentage}%; transform: translateX(-50%)`}
    ></span>
  </div>
  {#if name}<input type="hidden" {name} value={slider.value} />{/if}
</div>
