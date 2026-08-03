<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-29-metrics-derivation]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  A headline KPI tile for the client dashboard ([[FEEDLOT]]). Like MetricCard it
  only DISPLAYS a backend-derived number and honours the null-contract
  ([[adr-29-metrics-derivation]] rule 2): a value that cannot be computed renders
  "—" plus its reason, NEVER a fabricated zero. Adds a sub-line and an optional
  tone accent for the richer dashboard layout. Mounts with zero props (empty "—"
  state) and never throws ([[adr-22-showcase-ready-components]] rule 1). Copy via
  i18n at the call site ([[LOCALIZATION]]).
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
    sub = "",
    accent = "neutral",
  }: {
    label?: string;
    value?: string | number | null;
    currency?: string;
    unit?: string;
    fractionDigits?: number;
    notCalculable?: string;
    /** Second line under the value — context, not a fabricated trend. */
    sub?: string;
    /** Left border accent tone. */
    accent?: "neutral" | "primary" | "success" | "warning" | "negative";
  } = $props();

  const REASONS: Record<string, string> = {
    head_count_changed: "cambió el rodeo entre pesajes",
    no_measured_growth: "sin crecimiento medido",
    no_weight_gain: "sin aumento de peso",
    no_intake_in_period: "sin ingresos en el período",
    no_entries: "sin movimientos",
    no_weighings: "sin pesajes",
    no_metric: "métrica no disponible aún",
  };

  const numeric = $derived(
    value === null || value === undefined || value === "" ? null : Number(value),
  );
  const calculable = $derived(!notCalculable && numeric !== null && !Number.isNaN(numeric));
  const display = $derived(
    calculable ? formatNumber(numeric as number, currency, "es", fractionDigits) : "—",
  );
  const reason = $derived(notCalculable ? (REASONS[notCalculable] ?? notCalculable) : "");

  const ACCENTS: Record<string, string> = {
    neutral: "var(--border)",
    primary: "var(--primary)",
    success: "var(--success)",
    warning: "var(--warning)",
    negative: "var(--negative)",
  };
  const accentColor = $derived(ACCENTS[accent] ?? ACCENTS.neutral);
</script>

<Card.Root class="border-border/40 shadow-sm">
  <Card.Content class="flex flex-col gap-1 p-4" style={`border-left: 3px solid ${accentColor};`}>
    <span class="text-[0.7rem] font-semibold uppercase tracking-wide text-muted-foreground">{label}</span>
    <span class="text-2xl font-bold tabular-nums leading-tight">
      {display}{#if calculable && unit}<span class="ml-1 text-sm font-normal text-muted-foreground">{unit}</span>{/if}
    </span>
    {#if reason}
      <span class="text-xs text-muted-foreground">no calculable · {reason}</span>
    {:else if sub}
      <span class="text-xs text-muted-foreground">{sub}</span>
    {/if}
  </Card.Content>
</Card.Root>
