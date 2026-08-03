<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-29-metrics-derivation]] · [[adr-53-api-membrane]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[FEEDLOT]]
     API: [[API]]
     LIVE-DOC:END -->

<!--
  Weighing history per lot (or animal): pick a target and see every weighing
  listed AND graphed ([[FEEDLOT]], redesign). It only READS the derived growth
  series the backend computes (`GET /api/lots/{id}/growth/` and the animal twin,
  [[API]]) and plots it — it computes no metric of its own
  ([[adr-29-metrics-derivation]] rule 1). The ADG null-contract (`same_date`,
  `head_count_changed`) is surfaced honestly, never a filled zero (rule 2). Mounts
  with zero props and never throws; a bare mount fires NO request — the GET runs
  only on an explicit target choice ([[adr-22-showcase-ready-components]] rules 1–2).
  Colours are `.feedlot-app` tokens ([[DESIGN-SYSTEM]]); copy via i18n.
-->
<script lang="ts">
  import TrendChart from "$lib/components/feedlot/TrendChart.svelte";
  import { t } from "../../../i18n";

  let {
    lots = [],
    animals = [],
    publicBackendUrl = "",
  }: {
    lots?: Array<Record<string, any>>;
    animals?: Array<Record<string, any>>;
    publicBackendUrl?: string;
  } = $props();

  type Reading = {
    weighing: number;
    date: string;
    weight: string | number;
    head_count: number;
    weight_per_head: string | number;
    adg: string | number | null;
    not_calculable: string;
  };

  const targets = $derived([
    ...lots
      .filter((l) => (l.status ?? "active") === "active")
      .map((l) => ({ value: `lot:${l.id}`, label: `${t("feedlot_form_lot")} ${l.code ?? l.id}` })),
    ...animals
      .filter((a) => (a.status ?? "active") === "active")
      .map((a) => ({ value: `animal:${a.id}`, label: a.ear_tag ?? `#${a.id}` })),
  ]);

  let target = $state("");
  let readings = $state<Reading[]>([]);
  let loading = $state(false);
  let error = $state("");
  let loaded = $state(false);

  // Chart plots the per-head weight over time — the honest growth line (a lot
  // total moves for reasons unrelated to growth, adr-28 decision 2).
  const points = $derived(
    readings.map((r) => ({ value: Number(r.weight_per_head), label: r.date })),
  );

  function reasonLabel(reason: string): string {
    if (reason === "same_date") return t("weighing_adg_same_date");
    if (reason === "head_count_changed") return t("weighing_adg_head_changed");
    return "";
  }

  function fmt(value: string | number | null): string {
    if (value === null || value === "" || value === undefined) return "—";
    const n = Number(value);
    return Number.isNaN(n) ? String(value) : n.toLocaleString("es-AR", { maximumFractionDigits: 2 });
  }

  async function load(): Promise<void> {
    if (target === "") {
      readings = [];
      loaded = false;
      return;
    }
    const [kind, idStr] = target.split(":");
    const path = kind === "animal" ? "animals" : "lots";
    loading = true;
    error = "";
    try {
      const res = await fetch(`${publicBackendUrl}/api/${path}/${idStr}/growth/`, {
        credentials: "include",
      });
      if (!res.ok) {
        error = `${t("feedlot_form_error")} (${res.status})`;
        readings = [];
        return;
      }
      const data = await res.json();
      readings = Array.isArray(data) ? data : (data.results ?? []);
      loaded = true;
    } catch {
      error = t("feedlot_form_error");
      readings = [];
    } finally {
      loading = false;
    }
  }

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";
</script>

<div class="flex flex-col gap-4">
  <div class="flex flex-col gap-1.5">
    <label class="text-sm font-medium" for="wh-target">{t("weighing_history_pick")}</label>
    <select id="wh-target" class={inputClass} bind:value={target} onchange={load} disabled={loading}>
      <option value="">{t("feedlot_form_target_placeholder")}</option>
      {#each targets as opt (opt.value)}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </div>

  {#if loading}
    <p class="text-sm text-muted-foreground">{t("weighing_loading")}</p>
  {:else if error}
    <p class="text-sm text-destructive">{error}</p>
  {:else if target === ""}
    <div
      class="flex items-center justify-center rounded-xl px-6 py-10 text-center text-sm text-muted-foreground"
      style="background: var(--muted);"
    >
      {t("weighing_history_hint")}
    </div>
  {:else if loaded && readings.length === 0}
    <div
      class="flex items-center justify-center rounded-xl px-6 py-10 text-center text-sm text-muted-foreground"
      style="background: var(--muted);"
    >
      {t("weighing_history_empty")}
    </div>
  {:else if readings.length > 0}
    <!-- Chart: per-head weight over time -->
    <div class="rounded-xl p-4" style="background: var(--muted);">
      <p class="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {t("weighing_chart_label")}
      </p>
      <TrendChart points={points} height={120} ariaLabel={t("weighing_chart_label")} />
    </div>

    <!-- Table: every weighing listed -->
    <div class="overflow-x-auto">
      <table class="w-full border-collapse text-sm">
        <thead>
          <tr class="border-b text-left text-xs uppercase tracking-wide text-muted-foreground"
            style="border-color: var(--border);">
            <th class="py-2 pr-3 font-medium">{t("feedlot_form_date")}</th>
            <th class="py-2 pr-3 text-right font-medium">{t("feedlot_col_total_weight")}</th>
            <th class="py-2 pr-3 text-right font-medium">{t("feedlot_col_headcount")}</th>
            <th class="py-2 pr-3 text-right font-medium">{t("weighing_col_wph")}</th>
            <th class="py-2 text-right font-medium">{t("weighing_col_adg")}</th>
          </tr>
        </thead>
        <tbody>
          {#each readings as r (r.weighing)}
            <tr class="border-b" style="border-color: var(--hairline);">
              <td class="py-2 pr-3">{r.date}</td>
              <td class="py-2 pr-3 text-right tabular-nums">{fmt(r.weight)}</td>
              <td class="py-2 pr-3 text-right tabular-nums">{r.head_count}</td>
              <td class="py-2 pr-3 text-right tabular-nums">{fmt(r.weight_per_head)}</td>
              <td class="py-2 text-right tabular-nums">
                {#if r.adg !== null && r.adg !== undefined}
                  {fmt(r.adg)}
                {:else if r.not_calculable}
                  <span class="text-xs text-muted-foreground" title={reasonLabel(r.not_calculable)}>
                    {t("weighing_not_calculable")}
                  </span>
                {:else}
                  —
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
