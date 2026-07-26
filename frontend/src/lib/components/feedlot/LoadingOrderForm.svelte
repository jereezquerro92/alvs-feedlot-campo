<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Register a mixer loading order — the PLAN of what should be delivered to a pen for
  a ration ([[adr-33-feedyard-operating-loop]] decision 2). Writes only through the
  declared endpoint `POST /api/loading-orders/`, which routes to
  `register_loading_order`: it plans, it does NOT charge — the debit is the
  `FeedingEvent`'s, when the ration is actually served (decision 1). A bare mount
  performs NO request ([[adr-22-showcase-ready-components]] rule 2), mounts with zero
  props and never throws (rule 1). Session + CSRF per [[AUTH]].
-->
<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { t } from "../../../i18n";

  let {
    pens = [],
    rations = [],
    today = "",
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    pens?: Array<Record<string, any>>;
    rations?: Array<Record<string, any>>;
    today?: string;
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  const activePens = $derived(pens.filter((p) => (p.status ?? "active") === "active"));
  const activeRations = $derived(rations.filter((r) => (r.is_active ?? true) !== false));

  let pen = $state("");
  let ration = $state("");
  let plannedKg = $state("");
  let notes = $state("");
  let date = $state(today);
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const valid = $derived(
    pen !== "" && ration !== "" && plannedKg !== "" && Number(plannedKg) > 0 && date !== "",
  );

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    ok = false;
    const body: Record<string, unknown> = {
      pen: Number(pen),
      ration: Number(ration),
      planned_as_fed_kg: Number(plannedKg),
      date,
    };
    if (notes !== "") body.notes = notes;
    try {
      const res = await fetch(`${publicBackendUrl}/api/loading-orders/`, {
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
      plannedKg = "";
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
  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="lo-pen">{t("feedlot_form_pen")}</Label>
      <select id="lo-pen" class={inputClass} bind:value={pen} disabled={saving}>
        <option value="" disabled>{t("feedlot_form_pen_placeholder")}</option>
        {#each activePens as p (p.id)}
          <option value={String(p.id)}>{p.code ?? p.name ?? `#${p.id}`}</option>
        {/each}
      </select>
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="lo-ration">{t("feedlot_form_ration")}</Label>
      <select id="lo-ration" class={inputClass} bind:value={ration} disabled={saving}>
        <option value="" disabled>{t("feedlot_form_ration_placeholder")}</option>
        {#each activeRations as r (r.id)}
          <option value={String(r.id)}>{r.name ?? `#${r.id}`}</option>
        {/each}
      </select>
    </div>
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="lo-kg">{t("feedlot_form_planned_kg")}</Label>
      <Input id="lo-kg" type="number" min="0" step="0.01" bind:value={plannedKg} disabled={saving} />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="lo-date">{t("feedlot_form_date")}</Label>
      <Input id="lo-date" type="date" bind:value={date} disabled={saving} />
    </div>
  </div>

  <div class="flex flex-col gap-1.5">
    <Label for="lo-notes">{t("feedlot_form_notes")}</Label>
    <Input id="lo-notes" type="text" bind:value={notes} disabled={saving} />
  </div>

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_order")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
