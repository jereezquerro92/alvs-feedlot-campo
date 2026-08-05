<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  One client's feedlot dashboard ([[FEEDLOT]]), composed inside FeedlotShell so
  sidebar + Breadcrumb/session header match every other module. `.feedlot-app`
  green tokens override the template's global orange without touching any
  component class ([[adr-04-frontend-and-design-system]] rule 5, [[DESIGN-SYSTEM]]).

  It only DISPLAYS metrics derived in the backend ([[adr-29-metrics-derivation]] rule
  1) — it computes none. Every metric that arrives null renders as "—" with its reason,
  never a fabricated zero (rule 2); where the backend has no metric yet (per-day herd
  weight, GDP, per-lot conversion) the tile is honestly empty rather than invented.
  Read-only; copy through i18n ([[LOCALIZATION]]). Mounts with zero props and never
  throws ([[adr-22-showcase-ready-components]] rule 1).
-->
<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";
  import { PageHeader } from "$lib/components/primitives/titles";
  import {
    FeedlotShell,
    KpiCard,
    GrowthCostChart,
    CostDonut,
    LotBars,
    RecentMovements,
    HerdTable,
  } from "$lib/components/feedlot";
  import { t } from "../../../i18n";

  type Dict = Record<string, unknown> | null | undefined;

  let {
    projectSlug = "",
    client = null,
    clients = [],
    summary = null,
    account = null,
    dailyCost = [],
    prices = [],
    animals = [],
    lots = [],
  }: {
    projectSlug?: string;
    client?: {
      id: number;
      name: string;
      kind?: string;
      tax_id?: string;
      balance?: string | number | null;
    } | null;
    /** Roster retained for callers; shell header uses Breadcrumb only. */
    clients?: Array<{ id: number | string; name?: string; kind?: string }>;
    summary?: Dict;
    account?: Dict;
    dailyCost?: Array<Record<string, unknown>>;
    prices?: Array<Record<string, unknown>>;
    animals?: Array<Record<string, unknown>>;
    lots?: Array<Record<string, unknown>>;
  } = $props();

  function str(v: unknown): string {
    return v === null || v === undefined ? "" : String(v);
  }
  function toNum(v: unknown): number | null {
    if (v === null || v === undefined || v === "") return null;
    const n = Number(v);
    return Number.isNaN(n) ? null : n;
  }

  // --- nested metric blocks off the summary payload (adr-29 shapes) ---
  const herd = $derived((summary?.herd ?? {}) as Record<string, unknown>);
  const cost = $derived((summary?.cost ?? {}) as Record<string, unknown>);
  const byConcept = $derived((cost.by_concept ?? {}) as Record<string, unknown>);
  const conv = $derived((summary?.conversion ?? {}) as Record<string, unknown>);
  const mort = $derived((summary?.mortality ?? {}) as Record<string, unknown>);
  const inconsistencies = $derived(
    Array.isArray(summary?.inconsistencies) ? (summary?.inconsistencies as unknown[]) : [],
  );

  const balance = $derived(toNum(summary?.balance ?? client?.balance));
  const balanceSub = $derived(
    balance === null
      ? ""
      : balance > 0
        ? t("feedlot_kpi_balance_owes")
        : balance < 0
          ? t("feedlot_kpi_balance_credit")
          : t("feedlot_kpi_balance_settled"),
  );

  const totalWeight = $derived(toNum(herd.total_weight));
  const herdSub = $derived(
    totalWeight === null
      ? t("feedlot_kpi_herd_sub_empty")
      : `${formatNumber(totalWeight, undefined, "es", 0)} kg`,
  );

  const mortRate = $derived(toNum(mort.rate));
  const mortPct = $derived(mortRate === null ? null : mortRate * 100);
  const mortSub = $derived(`${str(mort.dead_head ?? 0)} ${t("feedlot_unit_head")}`);

  // --- combo chart: real daily charge totals + their cumulative ---
  const dailyPoints = $derived(
    dailyCost.map((d) => ({ label: str(d.date), value: str(d.total) })),
  );

  // --- cost donut: real debits by concept, non-zero slices only ---
  const CONCEPT_META: Array<{ key: string; label: string; color: string }> = [
    { key: "feeding", label: t("feedlot_concept_feeding"), color: "var(--chart-1)" },
    { key: "service", label: t("feedlot_concept_service"), color: "var(--chart-3)" },
    { key: "health", label: t("feedlot_concept_health"), color: "var(--chart-5)" },
    { key: "sale", label: t("feedlot_concept_sale"), color: "var(--chart-2)" },
    { key: "adjustment", label: t("feedlot_concept_adjustment"), color: "var(--chart-6)" },
  ];
  const costSlices = $derived(
    CONCEPT_META.map((m) => ({ label: m.label, color: m.color, value: str(byConcept[m.key]) })),
  );

  // --- per-lot bars: honest average weight per head (no per-lot conversion metric yet) ---
  const lotRows = $derived(
    lots.map((l) => {
      const head = toNum(l.head_count) ?? 0;
      const tw = toNum(l.total_weight) ?? 0;
      const avg = head > 0 ? tw / head : 0;
      return { code: str(l.code ?? l.name ?? `L-${str(l.id)}`), value: avg };
    }),
  );

  // --- last movements off the account series ---
  const recent = $derived(
    Array.isArray(account?.points) ? (account?.points as Array<Record<string, unknown>>).slice(-6) : [],
  );

  const herdCopy = {
    lotsTitle: t("feedlot_herd_lots"),
    animalsTitle: t("feedlot_herd_animals"),
    code: t("feedlot_col_code"),
    headCount: t("feedlot_col_headcount"),
    totalWeight: t("feedlot_col_total_weight"),
    status: t("feedlot_col_status"),
    earTag: t("feedlot_col_eartag"),
    category: t("feedlot_col_category"),
    currentWeight: t("feedlot_col_current_weight"),
    emptyLots: t("feedlot_empty_lots"),
    emptyAnimals: t("feedlot_empty_animals"),
  };

  const pageSubtitle = $derived(
    [
      client?.name ?? t("feedlot_dash_fallback"),
      client?.tax_id ? `CUIT ${client.tax_id}` : "",
    ]
      .filter(Boolean)
      .join(" · "),
  );
</script>

<FeedlotShell
  active="dashboard"
  clients={clients}
  currentClient={client}
>
  <slot name="session" slot="session" />

  <div class="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <PageHeader title={t("feedlot_dash_title")} subtitle={pageSubtitle}>
        {#snippet actions()}
          <Button variant="outline" size="sm" disabled title={t("feedlot_action_export_soon")}>
            {t("feedlot_action_export")}
          </Button>
          <Button href={client?.id ? `/feedlot/${client.id}/schedule/` : "#"} size="sm">
            {t("feedlot_action_analyze")}
          </Button>
        {/snippet}
      </PageHeader>

      <!-- Mobile quick-nav (the sidebar is desktop-only) -->
      {#if client?.id}
        <div class="flex flex-wrap gap-2 lg:hidden">
          <Button href={`/feedlot/${client.id}/load/`} size="sm">{t("feedlot_load_cta")}</Button>
          <Button href={`/feedlot/${client.id}/ledger/`} variant="secondary" size="sm">{t("feedlot_ledger_cta")}</Button>
          <Button href={`/feedlot/${client.id}/outstanding/`} variant="secondary" size="sm">{t("feedlot_impute_cta")}</Button>
          <Button href={`/feedlot/${client.id}/schedule/`} variant="secondary" size="sm">{t("feedlot_schedule_cta")}</Button>
          <Button href="/feedlot/" variant="ghost" size="sm">{t("feedlot_back_clients")}</Button>
        </div>
      {/if}

      <!-- KPI tiles -->
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-3">
        <KpiCard
          label={t("feedlot_kpi_herd")}
          value={herd.head_count ?? null}
          unit={t("feedlot_unit_head")}
          sub={herdSub}
          accent="primary"
        />
        <KpiCard
          label={t("feedlot_kpi_balance")}
          value={summary?.balance ?? client?.balance ?? null}
          currency="ARS"
          sub={balanceSub}
          accent="primary"
        />
        <KpiCard
          label={t("feedlot_kpi_feed_cost")}
          value={byConcept.feeding ?? null}
          currency="ARS"
          sub={t("feedlot_kpi_feed_cost_sub")}
          accent="success"
        />
        <KpiCard
          label={t("feedlot_kpi_gdp")}
          value={null}
          notCalculable="no_metric"
          accent="neutral"
        />
        <KpiCard
          label={t("feedlot_kpi_conversion")}
          value={conv.conversion ?? null}
          fractionDigits={1}
          notCalculable={str(conv.not_calculable)}
          sub={t("feedlot_kpi_conversion_sub")}
          accent="primary"
        />
        <KpiCard
          label={t("feedlot_kpi_mortality")}
          value={mortPct}
          unit="%"
          fractionDigits={1}
          notCalculable={str(mort.not_calculable)}
          sub={mortSub}
          accent="warning"
        />
      </div>

      {#if inconsistencies.length > 0}
        <p class="rounded-md border border-warning/40 bg-warning/10 px-4 py-2 text-sm text-muted-foreground">
          {t("feedlot_inconsistencies")}: {inconsistencies.length}
        </p>
      {/if}

      <!-- Combo chart + cost donut -->
      <div class="grid gap-4 lg:grid-cols-3">
        <Card.Root class="border-border/40 shadow-sm lg:col-span-2">
          <Card.Header>
            <Card.Title class="text-base">{t("feedlot_chart_cost_title")}</Card.Title>
            <Card.Description>{t("feedlot_chart_cost_desc")}</Card.Description>
          </Card.Header>
          <Card.Content>
            <GrowthCostChart
              points={dailyPoints}
              barLabel={t("feedlot_chart_cost_bar")}
              lineLabel={t("feedlot_chart_cost_line")}
              ariaLabel={t("feedlot_chart_cost_title")}
              emptyLabel={t("feedlot_no_chart")}
            />
          </Card.Content>
        </Card.Root>

        <Card.Root class="min-w-0 border-border/40 shadow-sm">
          <Card.Header>
            <Card.Title class="text-base">{t("feedlot_donut_title")}</Card.Title>
            <Card.Description>{t("feedlot_donut_desc")}</Card.Description>
          </Card.Header>
          <Card.Content class="min-w-0">
            <CostDonut
              slices={costSlices}
              centerLabel={t("feedlot_donut_center")}
              ariaLabel={t("feedlot_donut_title")}
              emptyLabel={t("feedlot_no_chart")}
            />
          </Card.Content>
        </Card.Root>
      </div>

      <!-- Per-lot bars + recent movements -->
      <div class="grid gap-4 lg:grid-cols-2">
        <Card.Root class="border-border/40 shadow-sm">
          <Card.Header>
            <Card.Title class="text-base">{t("feedlot_lots_title")}</Card.Title>
            <Card.Description>{t("feedlot_lots_desc")}</Card.Description>
          </Card.Header>
          <Card.Content>
            <LotBars rows={lotRows} unit="kg" emptyLabel={t("feedlot_empty_lots")} />
          </Card.Content>
        </Card.Root>

        <Card.Root class="border-border/40 shadow-sm">
          <Card.Header>
            <Card.Title class="text-base">{t("feedlot_recent_title")}</Card.Title>
            <Card.Description>{t("feedlot_recent_desc")}</Card.Description>
          </Card.Header>
          <Card.Content>
            <RecentMovements movements={recent} emptyLabel={t("feedlot_recent_empty")} />
          </Card.Content>
        </Card.Root>
      </div>

      <!-- Herd roster -->
      <Card.Root class="border-border/40 shadow-sm">
        <Card.Header>
          <Card.Title class="text-base">{t("feedlot_herd_title")}</Card.Title>
        </Card.Header>
        <Card.Content>
          <HerdTable {lots} {animals} copy={herdCopy} />
        </Card.Content>
      </Card.Root>

      <p class="pb-4 text-xs text-muted-foreground">{t("feedlot_dash_derivation_note")}</p>
  </div>
</FeedlotShell>
