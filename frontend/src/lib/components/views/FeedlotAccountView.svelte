<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-25-account-ledger]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[FEEDLOT]]
     LIVE-DOC:END -->

<!--
  The current-account module ([[FEEDLOT]], redesign). Module-first: you enter the
  module and pick a client in the topbar; the account is per-client so it shows a
  "pick a client" hint until one is selected. It only DISPLAYS the immutable ledger
  the backend derives at `GET /api/clients/{id}/ledger/` — it posts nothing and edits
  nothing (the account is corrected by new entries, never in place, [[adr-25-account-ledger]]
  rule 1). Balance is Σ debits − Σ credits, positive = the client owes (rule 2); the
  running balance is walked oldest→newest and shown newest-first. Each row is clickable
  and opens a receipt with the entry's full detail — concept, direction, unit_price ×
  quantity, and the `(source_kind, source_id)` back-pointer to the event that produced
  it (rule 8). Read-only; the receipt is a local UI panel, no fetch on open. Mounts with
  zero props and never throws ([[adr-22-showcase-ready-components]] rule 1); a bare mount
  performs no request (rule 2). Green `.feedlot-app` tokens ([[DESIGN-SYSTEM]]); copy via
  i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";
  import { t } from "../../../i18n";

  type Client = { id: number | string; name?: string; kind?: string };
  type Dict = Record<string, unknown> | null | undefined;
  type Entry = {
    id: number;
    account?: number | string;
    date?: string;
    direction?: string;
    amount?: string | number | null;
    concept?: string;
    source_kind?: string | null;
    source_id?: number | string | null;
    unit_price?: string | number | null;
    quantity?: string | number | null;
    description?: string;
    created_at?: string;
  };

  let {
    clients = [],
    currentClient = null,
    account = null,
    entries = [],
    publicBackendUrl = "",
  }: {
    clients?: Client[];
    currentClient?: Client | null;
    account?: Dict;
    entries?: Entry[];
    publicBackendUrl?: string;
  } = $props();

  const hasClient = $derived(currentClient !== null);

  // Rendered labels live only in the frontend output ([[LOCALIZATION]]); the model
  // stores the English keys.
  const CONCEPTS: Record<string, string> = {
    feeding: "Alimentación",
    health: "Sanidad",
    service: "Servicio",
    adjustment: "Ajuste",
    payment: "Pago",
    sale: "Venta",
  };
  // `source_kind` maps the entry to the event that produced it (adr-25 rule 8).
  const SOURCES: Record<string, string> = {
    feeding_event: "Alimentación (evento)",
    health_event: "Sanidad (evento)",
    field_task: "Tarea de campo",
    maintenance_event: "Mantenimiento",
    exit: "Salida (venta)",
    payment: "Pago",
    adjustment: "Ajuste manual",
  };

  function num(v: unknown): number | null {
    if (v === null || v === undefined || v === "") return null;
    const n = Number(v);
    return Number.isNaN(n) ? null : n;
  }
  function str(v: unknown): string {
    return v === null || v === undefined ? "" : String(v);
  }
  function conceptLabel(c: unknown): string {
    const key = str(c);
    return CONCEPTS[key] ?? key ?? "—";
  }
  function sourceLabel(kind: unknown): string {
    const key = str(kind);
    if (!key) return "";
    return SOURCES[key] ?? key;
  }

  // Prefer the backend-cached balance; fall back to the client's own balance field.
  const balance = $derived(
    num(account?.balance_cached) ?? num((currentClient as any)?.balance) ?? 0,
  );

  // Debit/credit totals for the header tiles — a presentation sum over the same
  // entries the table shows, not a second definition ([[adr-25-account-ledger]]).
  const totals = $derived.by(() => {
    let debit = 0;
    let credit = 0;
    for (const e of entries) {
      const amt = num(e.amount) ?? 0;
      if (e.direction === "debit") debit += amt;
      else credit += amt;
    }
    return { debit, credit };
  });

  // Entries come newest-first (`-date, -id`). Walk oldest→newest to accumulate the
  // running balance, then hand rows back newest-first. Each row keeps its original
  // entry so the receipt can show the full detail.
  const rows = $derived.by(() => {
    const chrono = entries.slice().reverse();
    let running = 0;
    const out = chrono.map((e) => {
      const amount = num(e.amount) ?? 0;
      const isDebit = e.direction === "debit";
      running += isDebit ? amount : -amount;
      return {
        id: e.id,
        entry: e,
        date: str(e.date),
        concept: conceptLabel(e.concept),
        description: str(e.description),
        debit: isDebit ? amount : null,
        credit: isDebit ? null : amount,
        balance: running,
      };
    });
    out.reverse();
    return out;
  });

  // Receipt modal — a local UI panel, opened on click, closed on backdrop/Escape.
  // No fetch happens here: the receipt shows data already in hand (adr-22 rule 2).
  let selected = $state<(typeof rows)[number] | null>(null);
  function openReceipt(r: (typeof rows)[number]) {
    selected = r;
  }
  function closeReceipt() {
    selected = null;
  }
  function onKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") closeReceipt();
  }

  const sel = $derived(selected?.entry ?? null);
  const selUnitPrice = $derived(num(sel?.unit_price));
  const selQuantity = $derived(num(sel?.quantity));
  const selHasCalc = $derived(selUnitPrice !== null && selQuantity !== null);
</script>

<svelte:window on:keydown={onKeydown} />

<FeedlotShell
  active="ledger"
  clients={clients}
  currentClient={currentClient}
  breadcrumb={t("feedlot_ledger_title")}
  switcherPattern={`/feedlot/cuenta?client={id}`}
>
  <slot name="session" slot="session" />

  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-bold tracking-tight">{t("feedlot_ledger_title")}</h1>
      <p class="text-sm text-muted-foreground">{t("feedlot_module_ledger_subtitle")}</p>
    </div>

    {#if !hasClient}
      <div class="rounded-2xl p-8 text-center" style="background: var(--card); border: var(--hairline) solid var(--border);">
        <p class="text-sm text-muted-foreground">{t("feedlot_module_ledger_pick_client_hint")}</p>
      </div>
    {:else}
      <!-- Balance / debit / credit tiles -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
          <div class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_ledger_balance")}</div>
          <div class="mt-1 text-2xl font-bold tabular-nums">{formatNumber(balance, "ARS")}</div>
          <div class="mt-1 text-xs text-muted-foreground">{t("feedlot_ledger_balance_hint")}</div>
        </div>
        <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
          <div class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_ledger_total_debit")}</div>
          <div class="mt-1 text-2xl font-bold tabular-nums">{formatNumber(totals.debit, "ARS")}</div>
        </div>
        <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
          <div class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_ledger_total_credit")}</div>
          <div class="mt-1 text-2xl font-bold tabular-nums text-success">{formatNumber(totals.credit, "ARS")}</div>
        </div>
      </div>

      <!-- Ledger table with clickable rows -->
      <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
        <div class="mb-1 flex flex-wrap items-baseline justify-between gap-2">
          <h2 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_ledger_movements")}</h2>
          <span class="text-xs text-muted-foreground">{t("feedlot_ledger_open_hint")}</span>
        </div>
        {#if rows.length === 0}
          <p class="py-6 text-center text-sm text-muted-foreground">{t("feedlot_ledger_empty")}</p>
        {:else}
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th class="pb-2 pr-4 font-semibold">{t("feedlot_ledger_col_date")}</th>
                  <th class="pb-2 pr-4 font-semibold">{t("feedlot_ledger_col_concept")}</th>
                  <th class="pb-2 pr-4 font-semibold">{t("feedlot_ledger_col_description")}</th>
                  <th class="pb-2 pr-4 font-semibold text-right">{t("feedlot_ledger_col_debit")}</th>
                  <th class="pb-2 pr-4 font-semibold text-right">{t("feedlot_ledger_col_credit")}</th>
                  <th class="pb-2 font-semibold text-right">{t("feedlot_ledger_col_balance")}</th>
                </tr>
              </thead>
              <tbody>
                {#each rows as r (r.id)}
                  <tr
                    class="feedlot-ledger-row cursor-pointer transition-colors"
                    style="border-top: var(--hairline) solid var(--border);"
                    onclick={() => openReceipt(r)}
                    tabindex="0"
                    role="button"
                    aria-label={`${r.concept} ${r.date}`}
                    onkeydown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openReceipt(r); } }}
                  >
                    <td class="py-2.5 pr-4 tabular-nums text-muted-foreground">{r.date || "—"}</td>
                    <td class="py-2.5 pr-4 font-medium">{r.concept}</td>
                    <td class="py-2.5 pr-4 text-muted-foreground">{r.description || "—"}</td>
                    <td class="py-2.5 pr-4 text-right tabular-nums">{r.debit === null ? "—" : formatNumber(r.debit, "ARS")}</td>
                    <td class="py-2.5 pr-4 text-right tabular-nums text-success">{r.credit === null ? "—" : formatNumber(r.credit, "ARS")}</td>
                    <td class="py-2.5 text-right font-semibold tabular-nums">{formatNumber(r.balance, "ARS")}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Receipt modal -->
  {#if selected && sel}
    <div
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      style="background: rgba(0,0,0,0.45);"
      onclick={closeReceipt}
      role="presentation"
    >
      <div
        class="w-full max-w-md rounded-2xl p-6 shadow-xl"
        style="background: var(--card); border: var(--hairline) solid var(--border);"
        onclick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={t("feedlot_ledger_receipt_title")}
      >
        <div class="mb-4 flex items-start justify-between gap-3">
          <div>
            <h3 class="text-lg font-bold tracking-tight">{t("feedlot_ledger_receipt_title")}</h3>
            <p class="text-xs text-muted-foreground">
              {t("feedlot_ledger_receipt_entry")} #{sel.id} · {selected.concept}
            </p>
          </div>
          <button
            type="button"
            class="grid size-8 shrink-0 place-items-center rounded-full transition-colors hover:bg-accent"
            style="border: var(--hairline) solid var(--border);"
            onclick={closeReceipt}
            aria-label={t("feedlot_ledger_receipt_close")}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              stroke-linecap="round" stroke-linejoin="round" class="size-4" aria-hidden="true">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Amount, front and centre -->
        <div class="mb-4 rounded-xl p-4 text-center" style="background: var(--canvas); border: var(--hairline) solid var(--border);">
          <div class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {sel.direction === "debit" ? t("feedlot_ledger_receipt_dir_debit") : t("feedlot_ledger_receipt_dir_credit")}
          </div>
          <div
            class="mt-1 text-3xl font-bold tabular-nums"
            style={sel.direction === "debit" ? "" : "color: var(--success);"}
          >
            {formatNumber(num(sel.amount) ?? 0, "ARS")}
          </div>
        </div>

        <dl class="flex flex-col gap-0 text-sm">
          <div class="flex justify-between gap-4 py-2" style="border-top: var(--hairline) solid var(--border);">
            <dt class="text-muted-foreground">{t("feedlot_ledger_col_date")}</dt>
            <dd class="font-medium tabular-nums">{selected.date || "—"}</dd>
          </div>
          <div class="flex justify-between gap-4 py-2" style="border-top: var(--hairline) solid var(--border);">
            <dt class="text-muted-foreground">{t("feedlot_ledger_col_concept")}</dt>
            <dd class="font-medium">{selected.concept}</dd>
          </div>
          {#if selHasCalc}
            <div class="flex justify-between gap-4 py-2" style="border-top: var(--hairline) solid var(--border);">
              <dt class="text-muted-foreground">{t("feedlot_ledger_receipt_calc")}</dt>
              <dd class="font-medium tabular-nums">
                {formatNumber(selQuantity ?? 0, undefined, "es", 2)} × {formatNumber(selUnitPrice ?? 0, "ARS", "es", 2)}
              </dd>
            </div>
          {/if}
          <div class="flex justify-between gap-4 py-2" style="border-top: var(--hairline) solid var(--border);">
            <dt class="text-muted-foreground">{t("feedlot_ledger_receipt_source")}</dt>
            <dd class="text-right font-medium">
              {#if sourceLabel(sel.source_kind)}
                {sourceLabel(sel.source_kind)}{#if sel.source_id} <span class="text-muted-foreground">#{sel.source_id}</span>{/if}
              {:else}
                <span class="text-muted-foreground">{t("feedlot_ledger_receipt_no_source")}</span>
              {/if}
            </dd>
          </div>
          {#if selected.description}
            <div class="flex justify-between gap-4 py-2" style="border-top: var(--hairline) solid var(--border);">
              <dt class="text-muted-foreground">{t("feedlot_ledger_col_description")}</dt>
              <dd class="text-right font-medium">{selected.description}</dd>
            </div>
          {/if}
          <div class="flex justify-between gap-4 py-2" style="border-top: var(--hairline) solid var(--border);">
            <dt class="text-muted-foreground">{t("feedlot_ledger_receipt_running")}</dt>
            <dd class="font-semibold tabular-nums">{formatNumber(selected.balance, "ARS")}</dd>
          </div>
          {#if sel.created_at}
            <div class="flex justify-between gap-4 py-2" style="border-top: var(--hairline) solid var(--border);">
              <dt class="text-muted-foreground">{t("feedlot_ledger_receipt_created")}</dt>
              <dd class="text-right text-xs text-muted-foreground tabular-nums">{sel.created_at}</dd>
            </div>
          {/if}
        </dl>

        <div class="mt-5 flex justify-end">
          <button
            type="button"
            class="rounded-lg px-4 py-2 text-sm font-semibold transition-colors hover:opacity-90"
            style="background: var(--primary); color: var(--primary-foreground);"
            onclick={closeReceipt}
          >
            {t("feedlot_ledger_receipt_close")}
          </button>
        </div>
      </div>
    </div>
  {/if}
</FeedlotShell>

<style>
  .feedlot-ledger-row:hover {
    background: var(--sidebar-hover-bg, var(--accent));
  }
</style>
