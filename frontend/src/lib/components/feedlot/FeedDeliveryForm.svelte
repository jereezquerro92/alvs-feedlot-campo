<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-53-api-membrane]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     API: [[API]]
     LIVE-DOC:END -->

<!--
  Register feed provided BY the client. Writes only through the declared endpoint
  `POST /api/feed-deliveries/`, which routes to `register_delivery`: it adds to the
  client's own feed stock and posts NO ledger entry — the client already provided it
  ([[adr-25-account-ledger]] rule 4). A later feeding with `origin=client_stock`
  draws it down uncharged. A bare mount performs NO request
  ([[adr-22-showcase-ready-components]] rule 2), mounts with zero props and never
  throws (rule 1). Session + CSRF per [[AUTH]].
-->
<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { DatePicker } from "$lib/components/form";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { t } from "../../../i18n";

  let {
    clientId = null,
    feedTypes = [],
    today = "",
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    clientId?: number | null;
    feedTypes?: Array<Record<string, any>>;
    today?: string;
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  let feedType = $state("");
  let quantity = $state("");
  let date = $state(today);
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const valid = $derived(
    clientId !== null && feedType !== "" && quantity !== "" && Number(quantity) > 0 && date !== "",
  );

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    ok = false;
    const body = {
      client: clientId,
      feed_type: Number(feedType),
      quantity: Number(quantity),
      date,
    };
    try {
      const res = await fetch(`${publicBackendUrl}/api/feed-deliveries/`, {
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
      quantity = "";
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
    <Label for="fd-feedtype">{t("feedlot_form_feed_type")}</Label>
    <select id="fd-feedtype" class={inputClass} bind:value={feedType} disabled={saving}>
      <option value="" disabled>{t("feedlot_form_feed_type_placeholder")}</option>
      {#each feedTypes as ft (ft.id)}
        <option value={String(ft.id)}>{ft.name}{ft.unit ? ` (${ft.unit})` : ""}</option>
      {/each}
    </select>
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="fd-qty">{t("feedlot_form_quantity")}</Label>
      <Input id="fd-qty" type="number" min="0" step="0.01" bind:value={quantity} disabled={saving} />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="fd-date">{t("feedlot_form_date")}</Label>
      <DatePicker
        id="fd-date"
        class="gap-0"
        bind:value={date}
        label={t("feedlot_form_date")}
        placeholder={t("feedlot_form_date_placeholder")}
        disabled={saving}
      />
    </div>
  </div>

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_delivery")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
