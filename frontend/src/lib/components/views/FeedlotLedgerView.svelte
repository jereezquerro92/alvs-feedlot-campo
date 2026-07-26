<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  One client's current-account screen ([[FEEDLOT]], [[adr-25-account-ledger]]). It
  only DISPLAYS the immutable ledger the backend derives — it posts nothing and
  edits nothing (the account is corrected by new entries, never in place, adr-25
  rule 1). The balance is Σ debits − Σ credits, positive = the client owes (adr-25
  rule 2); this view surfaces the cached balance plus the debit/credit totals and
  the full extract. Read-only; mounts with zero props and never throws
  ([[adr-22-showcase-ready-components]] rule 1). Copy Spanish, keys English
  ([[LOCALIZATION]]).
-->
<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { SectionTitle } from "$lib/components/primitives/titles";
  import { MetricCard, LedgerTable } from "$lib/components/feedlot";
  import { t } from "../../../i18n";

  type Dict = Record<string, unknown> | null | undefined;
  type Entry = {
    id: number;
    date?: string;
    direction?: string;
    amount?: string | number | null;
    concept?: string;
    description?: string;
  };

  let {
    projectSlug = "",
    client = null,
    account = null,
    entries = [],
  }: {
    projectSlug?: string;
    client?: {
      id: number;
      name: string;
      kind?: string;
      tax_id?: string;
      balance?: string | number | null;
    } | null;
    account?: Dict;
    entries?: Entry[];
  } = $props();

  const KINDS: Record<string, string> = {
    boarding: "Hotelería",
    own: "Hacienda propia",
  };

  function num(v: unknown): number | null {
    if (v === null || v === undefined || v === "") return null;
    const n = Number(v);
    return Number.isNaN(n) ? null : n;
  }

  // Prefer the backend-cached balance; fall back to the client's own balance field.
  const balance = $derived(num(account?.balance_cached) ?? num(client?.balance));

  // Debit/credit totals for the header tiles — a presentation sum over the same
  // entries the table shows, not a second definition of anything ([[adr-25-account-ledger]]).
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
</script>

<div class="min-h-screen flex flex-col">
  <header class="flex w-full items-center justify-between gap-4 px-6 pt-8 sm:px-10">
    <Badge variant="outline" class="text-sm font-semibold tracking-wide">{projectSlug}</Badge>
    <slot name="session" />
  </header>

  <main class="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-6 py-12">
    <div class="flex flex-col gap-2">
      <SectionTitle as="h1">{t("feedlot_ledger_title")}</SectionTitle>
      <div class="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        <span class="font-medium text-foreground">{client?.name ?? t("feedlot_dash_fallback")}</span>
        {#if client?.kind}
          <Badge variant="outline">{KINDS[client.kind] ?? client.kind}</Badge>
        {/if}
        {#if client?.tax_id}<span>CUIT {client.tax_id}</span>{/if}
      </div>
      <p class="max-w-2xl text-sm text-muted-foreground">{t("feedlot_ledger_intro")}</p>
    </div>

    <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
      <MetricCard label={t("feedlot_ledger_balance")} value={balance} currency="ARS" hint={t("feedlot_ledger_balance_hint")} />
      <MetricCard label={t("feedlot_ledger_total_debit")} value={totals.debit} currency="ARS" />
      <MetricCard label={t("feedlot_ledger_total_credit")} value={totals.credit} currency="ARS" />
    </div>

    <Card.Root class="border-border/40 shadow-sm">
      <Card.Header>
        <Card.Title class="text-base">{t("feedlot_ledger_movements")}</Card.Title>
        <Card.Description>{t("feedlot_ledger_movements_desc")}</Card.Description>
      </Card.Header>
      <Card.Content>
        <LedgerTable
          {entries}
          copy={{
            date: t("feedlot_ledger_col_date"),
            concept: t("feedlot_ledger_col_concept"),
            description: t("feedlot_ledger_col_description"),
            debit: t("feedlot_ledger_col_debit"),
            credit: t("feedlot_ledger_col_credit"),
            balance: t("feedlot_ledger_col_balance"),
          }}
          emptyLabel={t("feedlot_ledger_empty")}
        />
      </Card.Content>
    </Card.Root>

    <div class="flex flex-wrap gap-2">
      {#if client?.id}
        <Button href={`/feedlot/${client.id}/`} variant="secondary" size="sm">
          {t("feedlot_load_view_panel")}
        </Button>
        <Button href={`/feedlot/${client.id}/outstanding/`} variant="secondary" size="sm">
          {t("feedlot_impute_cta")}
        </Button>
      {/if}
      <Button href="/feedlot/" variant="secondary" size="sm">{t("feedlot_back_clients")}</Button>
    </div>
  </main>
</div>
