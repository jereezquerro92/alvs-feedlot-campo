<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-25-account-ledger]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The client's most recent account movements ([[FEEDLOT]], [[adr-25-account-ledger]]).
  Reads the real `account_evolution.points` it is handed: a DEBIT is money charged
  (shown negative), a CREDIT — a payment — is shown positive, matching the ledger's
  sign convention. No fabricated rows; empty points show an honest empty state.
  Copy via i18n at the call site. Mounts with zero props and never throws
  ([[adr-22-showcase-ready-components]] rule 1).
-->
<script lang="ts">
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";
  import { t } from "../../../i18n";

  let {
    movements = [],
    emptyLabel = "",
  }: {
    movements?: Array<{
      date?: string;
      concept?: string;
      direction?: string;
      amount?: string | number | null;
    }>;
    emptyLabel?: string;
  } = $props();

  const CONCEPTS: Record<string, string> = {
    feeding: t("feedlot_concept_feeding"),
    health: t("feedlot_concept_health"),
    service: t("feedlot_concept_service"),
    adjustment: t("feedlot_concept_adjustment"),
    sale: t("feedlot_concept_sale"),
    payment: t("feedlot_concept_payment"),
  };

  function num(v: unknown): number {
    if (v === null || v === undefined || v === "") return 0;
    const n = Number(v);
    return Number.isNaN(n) ? 0 : n;
  }
  function fmtDate(d: string): string {
    // ISO YYYY-MM-DD → DD/MM (feedlot reads dates day-first).
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d ?? "");
    return m ? `${m[3]}/${m[2]}` : (d ?? "");
  }

  const rows = $derived(
    movements
      .slice()
      .reverse()
      .map((p) => {
        const credit = String(p.direction ?? "").toLowerCase() === "credit";
        const amount = num(p.amount);
        return {
          date: fmtDate(String(p.date ?? "")),
          concept: CONCEPTS[String(p.concept ?? "")] ?? String(p.concept ?? ""),
          credit,
          amount,
        };
      }),
  );
  const hasData = $derived(rows.length > 0);
</script>

{#if hasData}
  <ul class="flex flex-col divide-y divide-border">
    {#each rows as r}
      <li class="flex items-center gap-3 py-2.5">
        <span class="w-12 shrink-0 text-xs tabular-nums text-muted-foreground">{r.date}</span>
        <span class="flex-1 truncate text-sm">{r.concept}</span>
        <span
          class="shrink-0 text-sm font-semibold tabular-nums"
          style={r.credit ? "color: var(--success);" : "color: var(--foreground);"}
        >
          {r.credit ? "+" : "−"}{formatNumber(r.amount, "ARS", "es", 0)}
        </span>
      </li>
    {/each}
  </ul>
{:else}
  <div class="flex h-24 items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground">
    {emptyLabel}
  </div>
{/if}
