<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  One client's feedlot dashboard ([[FEEDLOT]]). It only DISPLAYS metrics derived
  in the backend ([[adr-29-metrics-derivation]] rule 1) — it computes none. Every
  metric that arrives null renders as "—" with its reason, never as a fabricated
  zero (adr-29 rule 2). Read-only; copy through the i18n layer ([[LOCALIZATION]]).
  Mounts with zero props and never throws ([[adr-22-showcase-ready-components]] r1).
-->
<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { SectionTitle } from "$lib/components/primitives/titles";
  import { MetricCard, TrendChart, HerdTable } from "$lib/components/feedlot";
  import { t } from "../../../i18n";

  type Dict = Record<string, unknown> | null | undefined;

  let {
    projectSlug = "",
    client = null,
    summary = null,
    account = null,
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
    summary?: Dict;
    account?: Dict;
    prices?: Array<Record<string, unknown>>;
    animals?: Array<Record<string, unknown>>;
    lots?: Array<Record<string, unknown>>;
  } = $props();

  const KINDS: Record<string, string> = {
    boarding: "Hotelería",
    own: "Hacienda propia",
  };

  // --- pull nested metric blocks off the summary payload (adr-29 shapes) ---
  const herd = $derived((summary?.herd ?? {}) as Record<string, unknown>);
  const cost = $derived((summary?.cost ?? {}) as Record<string, unknown>);
  const conv = $derived((summary?.conversion ?? {}) as Record<string, unknown>);
  const mort = $derived((summary?.mortality ?? {}) as Record<string, unknown>);
  const inconsistencies = $derived(
    Array.isArray(summary?.inconsistencies) ? (summary?.inconsistencies as unknown[]) : [],
  );

  function str(v: unknown): string {
    return v === null || v === undefined ? "" : String(v);
  }
  function toNum(v: unknown): number | null {
    if (v === null || v === undefined || v === "") return null;
    const n = Number(v);
    return Number.isNaN(n) ? null : n;
  }

  // Mortality is a 0..1 fraction; show it as a percentage.
  const mortRate = $derived(toNum(mort.rate));
  const mortPct = $derived(mortRate === null ? null : mortRate * 100);

  // --- account balance series → chart points (oldest → newest) ---
  const accountPoints = $derived(
    Array.isArray(account?.points)
      ? (account?.points as Array<Record<string, unknown>>).map((p) => ({
          value: str(p.balance),
          label: str(p.date),
        }))
      : [],
  );

  // --- market prices: pick a category (Novillo preferred), plot its avg ---
  const priceCategory = $derived.by(() => {
    const cats = new Set(prices.map((p) => str(p.category)));
    if (cats.has("Novillo")) return "Novillo";
    return prices.length ? str(prices[0].category) : "";
  });
  const pricePoints = $derived(
    prices
      .filter((p) => str(p.category) === priceCategory)
      .slice()
      .sort((a, b) => str(a.date).localeCompare(str(b.date)))
      .map((p) => ({ value: str(p.price_avg), label: str(p.date) })),
  );
</script>

<div class="min-h-screen flex flex-col">
  <header class="flex w-full items-center justify-between gap-4 px-6 pt-8 sm:px-10">
    <Badge variant="outline" class="text-sm font-semibold tracking-wide">{projectSlug}</Badge>
    <slot name="session" />
  </header>

  <main class="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-6 py-12">
    <div class="flex flex-col gap-2">
      <SectionTitle as="h1">{client?.name ?? t("feedlot_dash_fallback")}</SectionTitle>
      <div class="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        {#if client?.kind}
          <Badge variant="outline">{KINDS[client.kind] ?? client.kind}</Badge>
        {/if}
        {#if client?.tax_id}<span>CUIT {client.tax_id}</span>{/if}
      </div>
      <p class="max-w-2xl text-sm text-muted-foreground">{t("feedlot_dash_intro")}</p>
      {#if client?.id}
        <div>
          <Button href={`/feedlot/${client.id}/load/`} size="sm">{t("feedlot_load_cta")}</Button>
        </div>
      {/if}
    </div>

    <!-- Metric tiles -->
    <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <MetricCard label={t("feedlot_metric_balance")} value={summary?.balance ?? client?.balance ?? null} currency="ARS" />
      <MetricCard label={t("feedlot_metric_head")} value={herd.head_count ?? null} unit={t("feedlot_unit_head")} />
      <MetricCard label={t("feedlot_metric_avg_weight")} value={herd.average_weight ?? null} unit="kg" />
      <MetricCard label={t("feedlot_metric_cost")} value={cost.total ?? null} currency="ARS" />
      <MetricCard
        label={t("feedlot_metric_conversion")}
        value={conv.conversion ?? null}
        fractionDigits={2}
        notCalculable={str(conv.not_calculable)}
        hint={t("feedlot_metric_conversion_hint")}
      />
      <MetricCard
        label={t("feedlot_metric_kilos_gained")}
        value={conv.kilos_gained ?? null}
        unit="kg"
        notCalculable={str(conv.not_calculable)}
      />
      <MetricCard
        label={t("feedlot_metric_mortality")}
        value={mortPct}
        unit="%"
        fractionDigits={1}
        notCalculable={str(mort.not_calculable)}
      />
      <MetricCard label={t("feedlot_metric_head_entered")} value={mort.entered_head ?? null} unit={t("feedlot_unit_head")} />
    </div>

    {#if inconsistencies.length > 0}
      <p class="rounded-md border border-border/60 bg-muted px-4 py-2 text-sm text-muted-foreground">
        {t("feedlot_inconsistencies")}: {inconsistencies.length}
      </p>
    {/if}

    <!-- Charts -->
    <div class="grid gap-4 md:grid-cols-2">
      <Card.Root class="border-border/40 shadow-sm">
        <Card.Header>
          <Card.Title class="text-base">{t("feedlot_chart_account")}</Card.Title>
          <Card.Description>{t("feedlot_chart_account_desc")}</Card.Description>
        </Card.Header>
        <Card.Content>
          <TrendChart points={accountPoints} ariaLabel={t("feedlot_chart_account")} emptyLabel={t("feedlot_no_chart")} />
        </Card.Content>
      </Card.Root>

      <Card.Root class="border-border/40 shadow-sm">
        <Card.Header>
          <Card.Title class="text-base">{t("feedlot_chart_prices")}</Card.Title>
          <Card.Description>
            {priceCategory ? `${t("feedlot_chart_prices_desc")} · ${priceCategory}` : t("feedlot_chart_prices_desc")}
          </Card.Description>
        </Card.Header>
        <Card.Content>
          <TrendChart points={pricePoints} ariaLabel={t("feedlot_chart_prices")} emptyLabel={t("feedlot_no_chart")} />
        </Card.Content>
      </Card.Root>
    </div>

    <!-- Herd -->
    <Card.Root class="border-border/40 shadow-sm">
      <Card.Header>
        <Card.Title class="text-base">{t("feedlot_herd_title")}</Card.Title>
      </Card.Header>
      <Card.Content>
        <HerdTable
          {lots}
          {animals}
          copy={{
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
          }}
        />
      </Card.Content>
    </Card.Root>

    <div>
      <Button href="/feedlot/" variant="secondary" size="sm">{t("feedlot_back_clients")}</Button>
    </div>
  </main>
</div>
