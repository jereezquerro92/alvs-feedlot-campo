<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  One derived-metric tile. Honours the null-contract ([[adr-29-metrics-derivation]]
  rule 2): a metric that cannot be computed renders "—" plus its reason, NEVER a
  zero. Mounts with zero props (renders the empty "—" state) and never throws
  ([[adr-22-showcase-ready-components]] rule 1).
-->
<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";

  let {
    label = "",
    value = null,
    currency = undefined,
    unit = "",
    fractionDigits = 0,
    notCalculable = "",
    hint = "",
  }: {
    label?: string;
    /** Raw metric — string (DecimalField) | number | null. */
    value?: string | number | null;
    currency?: string;
    unit?: string;
    fractionDigits?: number;
    /** Reason code from the backend; when set the tile shows "—" + the reason. */
    notCalculable?: string;
    hint?: string;
  } = $props();

  // Reason codes the metrics layer emits (adr-29), rendered in Spanish.
  const REASONS: Record<string, string> = {
    head_count_changed: "cambió el rodeo entre pesajes",
    no_measured_growth: "sin crecimiento medido",
    no_weight_gain: "sin aumento de peso",
    no_intake_in_period: "sin ingresos en el período",
    no_entries: "sin movimientos",
    no_weighings: "sin pesajes",
  };

  const numeric = $derived(
    value === null || value === undefined || value === ""
      ? null
      : Number(value),
  );
  const calculable = $derived(!notCalculable && numeric !== null && !Number.isNaN(numeric));
  const display = $derived(
    calculable ? formatNumber(numeric as number, currency, "es", fractionDigits) : "—",
  );
  const reason = $derived(notCalculable ? (REASONS[notCalculable] ?? notCalculable) : "");
</script>

<Card.Root class="border-border/40 shadow-sm">
  <Card.Content class="flex flex-col gap-1 p-4">
    <span class="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</span>
    <span class="text-2xl font-semibold tabular-nums">
      {display}{#if calculable && unit}<span class="ml-1 text-sm font-normal text-muted-foreground">{unit}</span>{/if}
    </span>
    {#if reason}
      <span class="text-xs text-muted-foreground">no calculable · {reason}</span>
    {:else if hint}
      <span class="text-xs text-muted-foreground">{hint}</span>
    {/if}
  </Card.Content>
</Card.Root>
