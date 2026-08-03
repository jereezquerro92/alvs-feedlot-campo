<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-53-api-membrane]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     API: [[API]]
     LIVE-DOC:END -->

<!--
  Enroll one animal OR one lot into a sanitary plan on a start date. Writes only
  through the declared endpoint `POST /api/plan-enrollments/`, which routes to
  `enroll_in_plan`: an immutable event that posts NO ledger entry — a plan is intent,
  not an applied input; billing stays with HealthEvent ([[adr-40-sanitary-plan-schedule]]
  decisions 1 and 4). The XOR (exactly one target) and the active-target / active-plan
  checks are the service's, never this form's (decision 5). A bare mount performs NO
  request ([[adr-22-showcase-ready-components]] rule 2), mounts with zero props and
  never throws (rule 1). Session + CSRF per [[AUTH]]. Copy Spanish ([[LOCALIZATION]]).
-->
<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { t } from "../../../i18n";

  let {
    clientId = null,
    plans = [],
    animals = [],
    lots = [],
    today = "",
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    clientId?: number | null;
    plans?: Array<Record<string, any>>;
    animals?: Array<Record<string, any>>;
    lots?: Array<Record<string, any>>;
    today?: string;
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  const activePlans = $derived(plans.filter((p) => (p.is_active ?? true) !== false));

  const targets = $derived([
    ...lots
      .filter((l) => (l.status ?? "active") === "active")
      .map((l) => ({ value: `lot:${l.id}`, label: `${t("feedlot_form_lot")} ${l.code ?? l.id}` })),
    ...animals
      .filter((a) => (a.status ?? "active") === "active")
      .map((a) => ({ value: `animal:${a.id}`, label: a.ear_tag ?? `#${a.id}` })),
  ]);

  let plan = $state("");
  let target = $state("");
  let startDate = $state(today);
  let notes = $state("");
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const valid = $derived(
    clientId !== null && plan !== "" && target !== "" && startDate !== "",
  );

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  function parseTarget(value: string): Record<string, number> {
    const [kind, idStr] = value.split(":");
    const id = Number(idStr);
    return kind === "animal" ? { animal: id } : { lot: id };
  }

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    ok = false;
    const body: Record<string, unknown> = {
      client: clientId,
      plan: Number(plan),
      ...parseTarget(target),
      start_date: startDate,
    };
    if (notes !== "") body.notes = notes;
    try {
      const res = await fetch(`${publicBackendUrl}/api/plan-enrollments/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": readCsrfTokenFromCookie(),
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        error = await readError(res);
        return;
      }
      ok = true;
      target = "";
      notes = "";
      onsaved?.();
    } catch {
      error = t("feedlot_form_error");
    } finally {
      saving = false;
    }
  }

  async function readError(res: Response): Promise<string> {
    try {
      const data = await res.json();
      return typeof data === "string" ? data : JSON.stringify(data);
    } catch {
      return `${t("feedlot_form_error")} (${res.status})`;
    }
  }
</script>

<form class="flex flex-col gap-3" onsubmit={submit}>
  <div class="flex flex-col gap-1.5">
    <Label for="e-plan">{t("feedlot_form_plan")}</Label>
    <select id="e-plan" class={inputClass} bind:value={plan} disabled={saving}>
      <option value="" disabled>{t("feedlot_form_plan_placeholder")}</option>
      {#each activePlans as p (p.id)}
        <option value={String(p.id)}>{p.name}</option>
      {/each}
    </select>
  </div>

  <div class="flex flex-col gap-1.5">
    <Label for="e-target">{t("feedlot_form_target")}</Label>
    <select id="e-target" class={inputClass} bind:value={target} disabled={saving}>
      <option value="" disabled>{t("feedlot_form_target_placeholder")}</option>
      {#each targets as opt (opt.value)}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="e-date">{t("feedlot_form_start_date")}</Label>
      <Input id="e-date" type="date" bind:value={startDate} disabled={saving} />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="e-notes">{t("feedlot_form_notes")}</Label>
      <Input id="e-notes" type="text" bind:value={notes} disabled={saving} />
    </div>
  </div>

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_enrollment")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
