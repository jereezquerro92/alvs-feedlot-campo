<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Payment imputation surface for one client ([[FEEDLOT]], [[adr-41-payment-allocation]]).
  Shows each charge with how much a payment covers it (outstanding derived on read,
  decision 4) and an imputation form that maps a payment to charges — automatic FIFO
  (decision 3) or explicit. Imputation posts NO ledger entry and moves NO balance
  (decision 1): it only records which charge a payment answers. Hydrated island
  (rung 3, [[adr-04-frontend-and-design-system]] rule 3) because the form owns submit
  state; the view holds no mutation itself and mounts safely with zero props
  ([[adr-22-showcase-ready-components]] rules 1–2). Renders inside FeedlotShell so
  chrome matches the rest of the green app. Copy Spanish, keys English
  ([[LOCALIZATION]]).
-->
<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import SessionBadge from "$lib/components/auth/SessionBadge.svelte";
  import { MetricCard, OutstandingTable, PaymentForm, PaymentImputationForm } from "$lib/components/feedlot";
  import type { Me } from "$lib/types/user";
  import { t } from "../../../i18n";

  let {
    client = null,
    account = null,
    charges = [],
    payments = [],
    allocations = [],
    today = "",
    publicBackendUrl = "",
    me = null,
    pending = false,
  }: {
    client?: { id: number; name: string; balance?: string | number | null } | null;
    account?: Record<string, unknown> | null;
    charges?: Array<Record<string, any>>;
    payments?: Array<Record<string, any>>;
    allocations?: Array<Record<string, any>>;
    today?: string;
    publicBackendUrl?: string;
    me?: Me | null;
    pending?: boolean;
  } = $props();

  function num(v: unknown): number | null {
    if (v === null || v === undefined || v === "") return null;
    const n = Number(v);
    return Number.isNaN(n) ? null : n;
  }

  const balance = $derived(num(account?.balance_cached) ?? num(client?.balance));
  const accountId = $derived(num(account?.id));
  // Positive balance = the client owes; negative = a credit balance / saldo a favor.
  const favor = $derived(balance !== null && balance < 0 ? -balance : 0);
  const totalOutstanding = $derived(
    charges.reduce((sum, c) => sum + (num(c.outstanding) ?? 0), 0),
  );

  function reload(): void {
    if (typeof window !== "undefined") window.location.reload();
  }
</script>

<FeedlotShell
  active="ledger"
  currentClient={client}
  breadcrumb={t("feedlot_impute_title")}
>
  <SessionBadge
    slot="session"
    {me}
    {pending}
    {publicBackendUrl}
    loginLabel={t("auth_login")}
    logoutLabel={t("auth_logout")}
  />

  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6">
    <div class="flex flex-col gap-2">
      <h1 class="text-2xl font-bold tracking-tight">{t("feedlot_impute_title")}</h1>
      <p class="text-sm font-medium text-foreground">{client?.name ?? t("feedlot_dash_fallback")}</p>
      <p class="max-w-2xl text-sm text-muted-foreground">{t("feedlot_impute_intro")}</p>
    </div>

    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <MetricCard label={t("feedlot_ledger_balance")} value={balance} currency="ARS" hint={t("feedlot_ledger_balance_hint")} />
      <MetricCard label={t("feedlot_impute_total_outstanding")} value={totalOutstanding} currency="ARS" hint={t("feedlot_impute_total_outstanding_hint")} />
      {#if favor > 0}
        <MetricCard label={t("feedlot_payment_favor")} value={favor} currency="ARS" hint={t("feedlot_payment_favor_card_hint")} />
      {/if}
    </div>

    <Card.Root class="border-border/40 shadow-sm">
      <Card.Header>
        <Card.Title class="text-base">{t("feedlot_payment_form_title")}</Card.Title>
        <Card.Description>{t("feedlot_payment_form_desc")}</Card.Description>
      </Card.Header>
      <Card.Content>
        <PaymentForm
          accountId={accountId}
          balance={balance}
          today={today}
          {publicBackendUrl}
          onsaved={reload}
        />
      </Card.Content>
    </Card.Root>

    <Card.Root class="border-border/40 shadow-sm">
      <Card.Header>
        <Card.Title class="text-base">{t("feedlot_impute_form_title")}</Card.Title>
        <Card.Description>{t("feedlot_impute_form_desc")}</Card.Description>
      </Card.Header>
      <Card.Content>
        <PaymentImputationForm
          clientId={client?.id ?? null}
          {payments}
          {allocations}
          {charges}
          {publicBackendUrl}
          onsaved={reload}
        />
      </Card.Content>
    </Card.Root>

    <Card.Root class="border-border/40 shadow-sm">
      <Card.Header>
        <Card.Title class="text-base">{t("feedlot_impute_charges")}</Card.Title>
        <Card.Description>{t("feedlot_impute_charges_desc")}</Card.Description>
      </Card.Header>
      <Card.Content>
        <OutstandingTable
          {charges}
          copy={{
            date: t("feedlot_ledger_col_date"),
            concept: t("feedlot_ledger_col_concept"),
            amount: t("feedlot_impute_col_amount"),
            allocated: t("feedlot_impute_col_allocated"),
            outstanding: t("feedlot_impute_col_outstanding"),
          }}
          emptyLabel={t("feedlot_impute_empty")}
        />
      </Card.Content>
    </Card.Root>

    <div class="flex flex-wrap gap-2">
      {#if client?.id}
        <Button href={`/feedlot/${client.id}/ledger/`} variant="secondary" size="sm">
          {t("feedlot_ledger_cta")}
        </Button>
      {/if}
      <Button href="/feedlot/" variant="secondary" size="sm">{t("feedlot_back_clients")}</Button>
    </div>
  </div>
</FeedlotShell>
