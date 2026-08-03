<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-24-feedlot-domain]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[FEEDLOT]]
     LIVE-DOC:END -->

<!--
  The extra-expenses module ([[adr-44-field-operational-roles]] decision 6). It loads
  charges the feedlot bills to a client's current account — labor (hours × price/hour),
  fuel (litres × price/litre), machinery, or other — each an immutable `ExpenseEvent`
  that posts a `service` DEBIT through the generic `(source_kind, source_id)` seam
  ([[adr-24-feedlot-domain]] rule 4), never a manual ledger debit ([[adr-25-account-ledger]]
  rule 1). Client-scoped: a charge always lands on a client's account, so you pick the
  client in the topbar first; the charge may target one lot or the whole client (lot
  null). The recent-expenses table below reflects what was posted. Mounts with zero props
  and never throws ([[adr-22-showcase-ready-components]] rule 1); the form performs no
  request on bare mount (rule 2). Green `.feedlot-app` tokens ([[DESIGN-SYSTEM]]); copy
  via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import { ExpenseForm } from "$lib/components/feedlot";
  import { t } from "../../../i18n";

  type Client = { id: number | string; name?: string; kind?: string };
  type Row = Record<string, any>;

  let {
    clients = [],
    currentClient = null,
    lots = [],
    expenses = [],
    today = "",
    publicBackendUrl = "",
  }: {
    clients?: Client[];
    currentClient?: Client | null;
    lots?: Row[];
    expenses?: Row[];
    today?: string;
    publicBackendUrl?: string;
  } = $props();

  const clientId = $derived(
    currentClient ? Number(currentClient.id) : null,
  );

  const catLabel: Record<string, string> = {
    labor: t("feedlot_expense_cat_labor"),
    fuel: t("feedlot_expense_cat_fuel"),
    machinery: t("feedlot_expense_cat_machinery"),
    other: t("feedlot_expense_cat_other"),
  };

  const lotLabel = (id: number | string | null | undefined): string => {
    if (id === null || id === undefined) return t("feedlot_expense_lot_all");
    return (
      lots.find((l) => String(l.id) === String(id))?.code ?? `#${id}`
    );
  };

  // Newest first; a reasonable window.
  const recent = $derived(
    [...expenses]
      .sort((a, b) => String(b.date ?? "").localeCompare(String(a.date ?? "")))
      .slice(0, 20),
  );

  function fmtMoney(v: number | string | undefined): string {
    if (v === undefined || v === null || v === "") return "—";
    const n = Number(v);
    if (Number.isNaN(n)) return String(v);
    return n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 2 });
  }

  function reload() {
    if (typeof window !== "undefined") window.location.reload();
  }
</script>

<FeedlotShell
  active="gastos"
  clients={clients}
  currentClient={currentClient}
  breadcrumb={t("feedlot_module_gastos_title")}
  switcherPattern={`/feedlot/gastos?client={id}`}
>
  <slot name="session" slot="session" />

  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-bold tracking-tight">{t("feedlot_module_gastos_title")}</h1>
      <p class="text-sm text-muted-foreground">{t("feedlot_module_gastos_subtitle")}</p>
    </div>

    {#if !currentClient}
      <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
        <p class="text-sm text-muted-foreground">{t("feedlot_expense_pick_client")}</p>
      </div>
    {:else}
      <div class="grid gap-5 lg:grid-cols-2">
        <!-- New expense -->
        <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
          <h2 class="mb-1 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_expense")}</h2>
          <p class="mb-4 text-xs text-muted-foreground">
            {t("feedlot_expense_charges_to")} <span class="font-medium text-foreground">{currentClient.name}</span>
          </p>
          <ExpenseForm
            clientId={clientId}
            lots={lots}
            today={today}
            publicBackendUrl={publicBackendUrl}
            onsaved={reload}
          />
        </div>

        <!-- Recent expenses -->
        <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
          <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_recent_expenses")}</h2>
          {#if recent.length === 0}
            <p class="text-sm text-muted-foreground">{t("feedlot_expense_recent_empty")}</p>
          {:else}
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-left text-xs uppercase tracking-wide text-muted-foreground">
                    <th class="pb-2 pr-4 font-semibold">{t("feedlot_expense_col_date")}</th>
                    <th class="pb-2 pr-4 font-semibold">{t("feedlot_expense_col_category")}</th>
                    <th class="pb-2 pr-4 font-semibold">{t("feedlot_expense_col_title")}</th>
                    <th class="pb-2 pr-4 font-semibold">{t("feedlot_expense_col_lot")}</th>
                    <th class="pb-2 font-semibold text-right">{t("feedlot_expense_col_total")}</th>
                  </tr>
                </thead>
                <tbody>
                  {#each recent as e (e.id)}
                    <tr style="border-top: var(--hairline) solid var(--border);">
                      <td class="py-2 pr-4">{e.date ?? "—"}</td>
                      <td class="py-2 pr-4">{catLabel[e.category] ?? e.category}</td>
                      <td class="py-2 pr-4">{e.title ?? "—"}</td>
                      <td class="py-2 pr-4 text-muted-foreground">{lotLabel(e.lot)}</td>
                      <td class="py-2 text-right tabular-nums">{fmtMoney(e.total_cost)}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</FeedlotShell>
