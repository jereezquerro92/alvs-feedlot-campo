<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-24-feedlot-domain]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[FEEDLOT]]
     LIVE-DOC:END -->

<!--
  A GENERAL, module-first data-entry surface ([[FEEDLOT]], redesign): you enter a
  thematic module (Ingresos-Egresos / Alimentos / Salud / Pesajes) WITHOUT first
  picking a client, then choose the client with the topbar dropdown — the module
  acts on that client. One island renders the whole green shell + the category's
  forms, so the new design is applied consistently instead of reverting to the old
  per-client submenu. Pure UI over existing per-client forms; the forms own the
  writes ([[adr-24-feedlot-domain]] — backend is the authority). Mounts with zero
  props and never throws ([[adr-22-showcase-ready-components]] rule 1). Colours are
  `.feedlot-app` tokens ([[DESIGN-SYSTEM]]); copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import FeedlotShell from "$lib/components/feedlot/FeedlotShell.svelte";
  import {
    IntakeForm,
    DeathForm,
    ExitForm,
    FeedingForm,
    FeedDeliveryForm,
    HealthEventForm,
    EnrollmentForm,
    SanitaryPlanForm,
    SanitaryScheduleTable,
    WeighingForm,
    WeighingHistory,
  } from "$lib/components/feedlot";
  import { t } from "../../../i18n";

  type Client = { id: number | string; name?: string; kind?: string };

  let {
    /** Which thematic module: "intake" | "feed" | "health" | "weighing". */
    module = "intake",
    /** Sidebar highlight key + route slug this module lives at. */
    navKey = "intake",
    slug = "hacienda",
    clients = [],
    currentClient = null,
    animals = [],
    lots = [],
    feedTypes = [],
    healthProducts = [],
    plans = [],
    schedule = null,
    today = "",
    publicBackendUrl = "",
  }: {
    module?: string;
    navKey?: string;
    slug?: string;
    clients?: Client[];
    currentClient?: Client | null;
    animals?: Array<Record<string, any>>;
    lots?: Array<Record<string, any>>;
    feedTypes?: Array<Record<string, any>>;
    healthProducts?: Array<Record<string, any>>;
    plans?: Array<Record<string, any>>;
    schedule?: Record<string, any> | null;
    today?: string;
    publicBackendUrl?: string;
  } = $props();

  const scheduleItems = $derived(
    Array.isArray(schedule?.items) ? (schedule?.items as Array<Record<string, any>>) : [],
  );

  const TITLES: Record<string, { title: string; subtitle: string }> = {
    intake: { title: t("feedlot_module_intake_title"), subtitle: t("feedlot_module_intake_subtitle") },
    feed: { title: t("feedlot_module_feed_title"), subtitle: t("feedlot_module_feed_subtitle") },
    health: { title: t("feedlot_module_health_title"), subtitle: t("feedlot_module_health_subtitle") },
    weighing: { title: t("feedlot_module_weighing_title"), subtitle: t("feedlot_module_weighing_subtitle") },
  };
  const head = $derived(TITLES[module] ?? TITLES.intake);

  const currentId = $derived(currentClient?.id ?? null);
  const clientIdNum = $derived(currentId === null ? null : Number(currentId));
  const clientKind = $derived(currentClient?.kind ?? "");

  // Reload so the freshly-posted event shows in the roster/metrics next paint.
  function reload() {
    if (typeof window !== "undefined") window.location.reload();
  }
</script>

<FeedlotShell
  active={navKey}
  clients={clients}
  currentClient={currentClient}
  breadcrumb={head.title}
  switcherPattern={`/feedlot/${slug}?client={id}`}
>
  <slot name="session" slot="session" />

  <div class="mx-auto flex w-full max-w-5xl flex-col gap-6">
    <!-- Page header -->
    <div class="flex flex-col gap-1">
      <h1 class="text-2xl font-bold tracking-tight">{head.title}</h1>
      <p class="text-sm text-muted-foreground">{head.subtitle}</p>
    </div>

    {#if !currentClient}
      <!-- No client chosen yet: module-first prompt (adr-22 safe empty state) -->
      <div
        class="flex flex-col items-center gap-3 rounded-2xl px-6 py-14 text-center"
        style="background: var(--card); border: var(--hairline) dashed var(--border);"
      >
        <span class="grid size-12 place-items-center rounded-full" style="background: var(--muted);">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
            stroke-linecap="round" stroke-linejoin="round" class="size-6 text-muted-foreground" aria-hidden="true">
            <path d="m6 9 6 6 6-6" />
          </svg>
        </span>
        <p class="text-base font-semibold">{t("feedlot_module_pick_client")}</p>
        <p class="max-w-sm text-sm text-muted-foreground">{t("feedlot_module_pick_client_hint")}</p>
      </div>
    {:else}
      <div class="grid gap-5 lg:grid-cols-2">
        {#if module === "intake"}
          <div class="lg:col-span-2 grid gap-5 lg:grid-cols-2">
            <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
              <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_intake")}</h2>
              <IntakeForm clientId={clientIdNum} lots={lots} today={today} publicBackendUrl={publicBackendUrl} onsaved={reload} />
            </div>
            <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
              <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_death")}</h2>
              <DeathForm animals={animals} lots={lots} today={today} publicBackendUrl={publicBackendUrl} onsaved={reload} />
            </div>
            <div class="rounded-2xl p-5 lg:col-span-2" style="background: var(--card); border: var(--hairline) solid var(--border);">
              <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_exit")}</h2>
              <ExitForm animals={animals} lots={lots} clientKind={clientKind} today={today} publicBackendUrl={publicBackendUrl} onsaved={reload} />
            </div>
          </div>
        {:else if module === "feed"}
          <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
            <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_feeding")}</h2>
            <FeedingForm clientId={clientIdNum} animals={animals} lots={lots} feedTypes={feedTypes} today={today} publicBackendUrl={publicBackendUrl} onsaved={reload} />
          </div>
          <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
            <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_delivery")}</h2>
            <FeedDeliveryForm clientId={clientIdNum} feedTypes={feedTypes} today={today} publicBackendUrl={publicBackendUrl} onsaved={reload} />
          </div>
        {:else if module === "health"}
          <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
            <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_health_event")}</h2>
            <HealthEventForm clientId={clientIdNum} animals={animals} lots={lots} healthProducts={healthProducts} today={today} publicBackendUrl={publicBackendUrl} onsaved={reload} />
          </div>
          <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
            <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_enrollment")}</h2>
            <EnrollmentForm clientId={clientIdNum} plans={plans} animals={animals} lots={lots} today={today} publicBackendUrl={publicBackendUrl} onsaved={reload} />
          </div>
          <div class="rounded-2xl p-5 lg:col-span-2" style="background: var(--card); border: var(--hairline) solid var(--border);">
            <h2 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_plan")}</h2>
            <p class="mb-4 text-xs text-muted-foreground">{t("feedlot_module_group_plan_hint")}</p>
            <SanitaryPlanForm healthProducts={healthProducts} publicBackendUrl={publicBackendUrl} onsaved={reload} />
          </div>
          <div class="rounded-2xl p-5 lg:col-span-2" style="background: var(--card); border: var(--hairline) solid var(--border);">
            <h2 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_calendar")}</h2>
            <p class="mb-4 text-xs text-muted-foreground">{t("feedlot_module_group_calendar_hint")}</p>
            <SanitaryScheduleTable
              items={scheduleItems}
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
          </div>
        {:else if module === "weighing"}
          <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
            <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_weighing")}</h2>
            <WeighingForm animals={animals} lots={lots} today={today} publicBackendUrl={publicBackendUrl} onsaved={reload} />
          </div>
          <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
            <h2 class="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">{t("feedlot_module_group_weighing_history")}</h2>
            <WeighingHistory animals={animals} lots={lots} publicBackendUrl={publicBackendUrl} />
          </div>
        {/if}
      </div>
    {/if}
  </div>
</FeedlotShell>
