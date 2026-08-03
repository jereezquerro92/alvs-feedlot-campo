<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  One client's sanitary calendar ([[FEEDLOT]], [[adr-40-sanitary-plan-schedule]]).
  It DISPLAYS the schedule the backend derives (`GET /api/plan-enrollments/schedule/`)
  — applied / pending / upcoming per dose (decision 3) — and lets the operator enroll a
  target into a plan (`POST /api/plan-enrollments/`, decision 1). Enrolling posts NO
  ledger entry: a plan is intent, billing stays with HealthEvent (decision 4). The
  pending tile is a presentation count over the derived items, not a second definition.
  Mounts with zero props and never throws ([[adr-22-showcase-ready-components]] rule 1).
  Copy Spanish, keys English ([[LOCALIZATION]]).
-->
<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import { MetricCard, SanitaryScheduleTable, EnrollmentForm } from "$lib/components/feedlot";
  import { t } from "../../../i18n";

  type Dict = Record<string, unknown> | null | undefined;

  let {
    client = null,
    schedule = null,
    plans = [],
    animals = [],
    lots = [],
    today = "",
    publicBackendUrl = "",
  }: {
    client?: {
      id: number;
      name: string;
      kind?: string;
      tax_id?: string;
    } | null;
    schedule?: Dict;
    plans?: Array<Record<string, unknown>>;
    animals?: Array<Record<string, unknown>>;
    lots?: Array<Record<string, unknown>>;
    today?: string;
    publicBackendUrl?: string;
  } = $props();

  const KINDS: Record<string, string> = {
    boarding: "Hotelería",
    own: "Hacienda propia",
  };

  const items = $derived(
    Array.isArray(schedule?.items) ? (schedule?.items as Array<Record<string, unknown>>) : [],
  );
  const pendingCount = $derived(
    typeof schedule?.pending_count === "number" ? (schedule?.pending_count as number) : items.filter((i) => i.status === "pending").length,
  );

  // After a successful enrollment the derived schedule changes; a full reload is the
  // simplest honest refresh (the calendar is SSR-derived, never held client-side).
  function reload(): void {
    if (typeof window !== "undefined") window.location.reload();
  }
</script>

<FeedlotShell
  active="sanitary"
  currentClient={client}
  breadcrumb={t("feedlot_schedule_title")}
>
  <slot name="session" slot="session" />

  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6">
    <div class="flex flex-col gap-2">
      <h1 class="text-2xl font-bold tracking-tight">{t("feedlot_schedule_title")}</h1>
      <div class="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        <span class="font-medium text-foreground">{client?.name ?? t("feedlot_dash_fallback")}</span>
        {#if client?.kind}
          <Badge variant="outline">{KINDS[client.kind] ?? client.kind}</Badge>
        {/if}
        {#if client?.tax_id}<span>CUIT {client.tax_id}</span>{/if}
      </div>
      <p class="max-w-2xl text-sm text-muted-foreground">{t("feedlot_schedule_intro")}</p>
    </div>

    <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
      <MetricCard label={t("feedlot_schedule_pending")} value={pendingCount} unit={t("feedlot_schedule_unit_doses")} hint={t("feedlot_schedule_pending_hint")} />
      <MetricCard label={t("feedlot_schedule_total")} value={items.length} unit={t("feedlot_schedule_unit_doses")} />
    </div>

    <Card.Root class="border-border/40 shadow-sm">
      <Card.Header>
        <Card.Title class="text-base">{t("feedlot_schedule_calendar")}</Card.Title>
        <Card.Description>{t("feedlot_schedule_calendar_desc")}</Card.Description>
      </Card.Header>
      <Card.Content>
        <SanitaryScheduleTable
          {items}
          copy={{
            plan: t("feedlot_schedule_col_plan"),
            target: t("feedlot_schedule_col_target"),
            product: t("feedlot_schedule_col_product"),
            due: t("feedlot_schedule_col_due"),
            dose: t("feedlot_schedule_col_dose"),
            status: t("feedlot_schedule_col_status"),
          }}
          statusLabels={{
            applied: t("feedlot_schedule_status_applied"),
            pending: t("feedlot_schedule_status_pending"),
            upcoming: t("feedlot_schedule_status_upcoming"),
          }}
          emptyLabel={t("feedlot_schedule_empty")}
        />
      </Card.Content>
    </Card.Root>

    <Card.Root class="border-border/40 shadow-sm">
      <Card.Header>
        <Card.Title class="text-base">{t("feedlot_schedule_enroll_title")}</Card.Title>
        <Card.Description>{t("feedlot_schedule_enroll_desc")}</Card.Description>
      </Card.Header>
      <Card.Content>
        <EnrollmentForm
          clientId={client?.id ?? null}
          {plans}
          {animals}
          {lots}
          {today}
          {publicBackendUrl}
          onsaved={reload}
        />
      </Card.Content>
    </Card.Root>

    <div class="flex flex-wrap gap-2">
      {#if client?.id}
        <Button href={`/feedlot/${client.id}/`} variant="secondary" size="sm">
          {t("feedlot_load_view_panel")}
        </Button>
      {/if}
      <Button href="/feedlot/" variant="secondary" size="sm">{t("feedlot_back_clients")}</Button>
    </div>
  </div>
</FeedlotShell>
