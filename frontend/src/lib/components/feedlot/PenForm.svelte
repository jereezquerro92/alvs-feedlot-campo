<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Create a corral (`Pen`) — an editable feedyard catalog ([[adr-33-feedyard-operating-loop]]
  decision 5, [[adr-49-domain-layer-and-growth-by-addition]] rule 3). Writes only through the declared
  endpoint `POST /api/pens/` (a plain ModelViewSet create); a Pen posts NO ledger
  entry — feedyard plans and monitors, it never charges (adr-33 decision 1). This
  form exists because the loading-order form needs pens to choose from: with zero
  pens its dropdown is empty and it can never become valid (task #21). A bare mount
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
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  let code = $state("");
  let name = $state("");
  let capacity = $state("");
  let status = $state("active");
  let notes = $state("");
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const valid = $derived(code.trim() !== "");

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    ok = false;
    const body: Record<string, unknown> = { code: code.trim(), status };
    if (name.trim() !== "") body.name = name.trim();
    if (capacity !== "" && Number(capacity) > 0) body.capacity_head = Number(capacity);
    if (notes.trim() !== "") body.notes = notes.trim();
    try {
      const res = await fetch(`${publicBackendUrl}/api/pens/`, {
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
      code = "";
      name = "";
      capacity = "";
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
      <Label for="pen-code">{t("feedlot_form_pen_code")}</Label>
      <Input id="pen-code" type="text" bind:value={code} disabled={saving} />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="pen-name">{t("feedlot_form_pen_name")}</Label>
      <Input id="pen-name" type="text" bind:value={name} disabled={saving} />
    </div>
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="pen-cap">{t("feedlot_form_pen_capacity")}</Label>
      <Input id="pen-cap" type="number" min="0" step="1" bind:value={capacity} disabled={saving} />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="pen-status">{t("feedlot_form_pen_status")}</Label>
      <select id="pen-status" class={inputClass} bind:value={status} disabled={saving}>
        <option value="active">{t("feedlot_form_pen_status_active")}</option>
        <option value="inactive">{t("feedlot_form_pen_status_inactive")}</option>
      </select>
    </div>
  </div>

  <div class="flex flex-col gap-1.5">
    <Label for="pen-notes">{t("feedlot_form_notes")}</Label>
    <Input id="pen-notes" type="text" bind:value={notes} disabled={saving} />
  </div>

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_pen")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
