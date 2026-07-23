<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Register a feeding for one animal OR one lot. Writes only through the declared
  endpoint `POST /api/feedings/`, which routes to the `register_feeding` service:
  `origin=own_stock` posts a debit + an out movement, `origin=client_stock` posts
  only the movement and no charge ([[adr-25-account-ledger]] rule 4) — this form
  never decides that, it only reports the fact. A bare mount performs NO request
  ([[adr-22-showcase-ready-components]] rule 2). Mounts with zero props and never
  throws (rule 1). Session + CSRF per the app's write pattern ([[AUTH]]).
-->
<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { t } from "../../../i18n";

  let {
    clientId = null,
    animals = [],
    lots = [],
    feedTypes = [],
    today = "",
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    clientId?: number | null;
    animals?: Array<Record<string, any>>;
    lots?: Array<Record<string, any>>;
    feedTypes?: Array<Record<string, any>>;
    today?: string;
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  const targets = $derived([
    ...lots
      .filter((l) => (l.status ?? "active") === "active")
      .map((l) => ({ value: `lot:${l.id}`, label: `${t("feedlot_form_lot")} ${l.code ?? l.id}` })),
    ...animals
      .filter((a) => (a.status ?? "active") === "active")
      .map((a) => ({ value: `animal:${a.id}`, label: a.ear_tag ?? `#${a.id}` })),
  ]);

  let target = $state("");
  let feedType = $state("");
  let quantity = $state("");
  let unitPrice = $state("");
  let origin = $state("own_stock");
  let date = $state(today);
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const valid = $derived(
    clientId !== null &&
      target !== "" &&
      feedType !== "" &&
      quantity !== "" &&
      Number(quantity) > 0 &&
      unitPrice !== "" &&
      Number(unitPrice) >= 0 &&
      date !== "",
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
      ...parseTarget(target),
      feed_type: Number(feedType),
      quantity: Number(quantity),
      unit_price: Number(unitPrice),
      origin,
      date,
    };
    try {
      const res = await fetch(`${publicBackendUrl}/api/feedings/`, {
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
    <Label for="f-target">{t("feedlot_form_target")}</Label>
    <select id="f-target" class={inputClass} bind:value={target} disabled={saving}>
      <option value="" disabled>{t("feedlot_form_target_placeholder")}</option>
      {#each targets as opt (opt.value)}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </div>

  <div class="flex flex-col gap-1.5">
    <Label for="f-feedtype">{t("feedlot_form_feed_type")}</Label>
    <select id="f-feedtype" class={inputClass} bind:value={feedType} disabled={saving}>
      <option value="" disabled>{t("feedlot_form_feed_type_placeholder")}</option>
      {#each feedTypes as ft (ft.id)}
        <option value={String(ft.id)}>{ft.name}{ft.unit ? ` (${ft.unit})` : ""}</option>
      {/each}
    </select>
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="f-qty">{t("feedlot_form_quantity")}</Label>
      <Input id="f-qty" type="number" min="0" step="0.01" bind:value={quantity} disabled={saving} />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="f-price">{t("feedlot_form_unit_price")}</Label>
      <Input id="f-price" type="number" min="0" step="0.01" bind:value={unitPrice} disabled={saving} />
    </div>
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="f-origin">{t("feedlot_form_origin")}</Label>
      <select id="f-origin" class={inputClass} bind:value={origin} disabled={saving}>
        <option value="own_stock">{t("feedlot_form_origin_own")}</option>
        <option value="client_stock">{t("feedlot_form_origin_client")}</option>
      </select>
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="f-date">{t("feedlot_form_date")}</Label>
      <Input id="f-date" type="date" bind:value={date} disabled={saving} />
    </div>
  </div>

  <p class="text-xs text-muted-foreground">
    {origin === "own_stock" ? t("feedlot_form_origin_own_hint") : t("feedlot_form_origin_client_hint")}
  </p>

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_feeding")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
