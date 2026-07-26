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
  ([[adr-22-showcase-ready-components]] rules 1–2). Copy Spanish, keys English
  ([[LOCALIZATION]]).
-->
<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { SectionTitle } from "$lib/components/primitives/titles";
  import SessionBadge from "$lib/components/auth/SessionBadge.svelte";
  import { MetricCard, OutstandingTable, PaymentImputationForm } from "$lib/components/feedlot";
  import type { Me } from "$lib/types/user";
  import { t } from "../../../i18n";

  let {
    projectSlug = "",
    client = null,
    account = null,
    charges = [],
    payments = [],
    allocations = [],
    publicBackendUrl = "",
    me = null,
    pending = false,
  }: {
    projectSlug?: string;
    client?: { id: number; name: string; balance?: string | number | null } | null;
    account?: Record<string, unknown> | null;
    charges?: Array<Record<string, any>>;
    payments?: Array<Record<string, any>>;
    allocations?: Array<Record<string, any>>;
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
  const totalOutstanding = $derived(
    charges.reduce((sum, c) => sum + (num(c.outstanding) ?? 0), 0),
  );

  function reload(): void {
    if (typeof window !== "undefined") window.location.reload();
  }
</script>

<div class="min-h-screen flex flex-col">
  <header class="flex w-full items-center justify-between gap-4 px-6 pt-8 sm:px-10">
    <Badge variant="outline" class="text-sm font-semibold tracking-wide">{projectSlug}</Badge>
    <SessionBadge
      {me}
      {pending}
      {publicBackendUrl}
      loginLabel={t("auth_login")}
      logoutLabel={t("auth_logout")}
    />
  </header>

  <main class="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-6 py-12">
    <div class="flex flex-col gap-2">
      <SectionTitle as="h1">{t("feedlot_impute_title")}</SectionTitle>
      <p class="text-sm font-medium text-foreground">{client?.name ?? t("feedlot_dash_fallback")}</p>
      <p class="max-w-2xl text-sm text-muted-foreground">{t("feedlot_impute_intro")}</p>
    </div>

    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <MetricCard label={t("feedlot_ledger_balance")} value={balance} currency="ARS" hint={t("feedlot_ledger_balance_hint")} />
      <MetricCard label={t("feedlot_impute_total_outstanding")} value={totalOutstanding} currency="ARS" hint={t("feedlot_impute_total_outstanding_hint")} />
    </div>

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
  </main>
</div>
