<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Register an exit (sale/transfer/other) for one animal OR one lot
  ([[adr-26-livestock-individual-and-lot]] rule 3 — exactly one target). Writes
  only through the declared endpoint `POST /api/exits/`, which routes to the domain
  service. A `kind=sale` exit settles through the ledger, differentiated by the
  client's kind ([[adr-43-sale-settlement]]): a BOARDING client sells its own cattle
  and the feedlot charges an engorde commission (a `service` debit) — this form shows
  the commission-% field; an OWN client's sale is the feedlot's and posts a `sale`
  credit (no commission). Deaths and non-sale exits post nothing
  ([[adr-28-animal-lifecycle-and-sanitary]] rule 3). A bare mount performs NO request
  ([[adr-22-showcase-ready-components]] rule 2), mounts with zero props and never
  throws (rule 1). CSRF per [[AUTH]].
-->
<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { t } from "../../../i18n";

  let {
    animals = [],
    lots = [],
    clientKind = "",
    today = "",
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    animals?: Array<Record<string, any>>;
    lots?: Array<Record<string, any>>;
    clientKind?: string;
    today?: string;
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  const kinds = [
    { value: "sale", label: "Venta" },
    { value: "transfer", label: "Retiro" },
    { value: "other", label: "Otro" },
  ];

  const targets = $derived([
    ...lots
      .filter((l) => (l.status ?? "active") === "active")
      .map((l) => ({ value: `lot:${l.id}`, label: `${t("feedlot_form_lot")} ${l.code ?? l.id}` })),
    ...animals
      .filter((a) => (a.status ?? "active") === "active")
      .map((a) => ({ value: `animal:${a.id}`, label: a.ear_tag ?? `#${a.id}` })),
  ]);

  let target = $state("");
  let kind = $state("sale");
  let destination = $state("");
  let headCount = $state("");
  let weight = $state("");
  let salePrice = $state("");
  let commission = $state("");
  let date = $state(today);
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const isLot = $derived(target.startsWith("lot:"));
  // Own-cattle sales post a credit and never carry a commission (adr-43); the
  // commission-% field is shown only for a boarding-client sale. An unknown kind
  // ("") falls to the boarding side, the common case.
  const isOwn = $derived(clientKind === "own");
  const isSale = $derived(kind === "sale");
  const valid = $derived(target !== "" && date !== "");

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  function parseTarget(value: string): Record<string, number> {
    const [k, idStr] = value.split(":");
    const id = Number(idStr);
    return k === "animal" ? { animal: id } : { lot: id };
  }

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    ok = false;
    const body: Record<string, unknown> = { ...parseTarget(target), date, kind };
    if (destination !== "") body.destination = destination;
    if (isLot && headCount !== "") body.head_count = Number(headCount);
    if (weight !== "") body.weight = Number(weight);
    if (salePrice !== "") body.sale_price_per_kg = Number(salePrice);
    // Only a boarding sale carries an engorde commission; own sales ignore it (adr-43).
    if (isSale && !isOwn && commission !== "") body.commission_pct = Number(commission);
    try {
      const res = await fetch(`${publicBackendUrl}/api/exits/`, {
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
      destination = "";
      headCount = "";
      weight = "";
      salePrice = "";
      commission = "";
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
    <Label for="x-target">{t("feedlot_form_target")}</Label>
    <select id="x-target" class={inputClass} bind:value={target} disabled={saving}>
      <option value="" disabled>{t("feedlot_form_target_placeholder")}</option>
      {#each targets as opt (opt.value)}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="x-kind">{t("feedlot_form_exit_kind")}</Label>
      <select id="x-kind" class={inputClass} bind:value={kind} disabled={saving}>
        {#each kinds as k (k.value)}
          <option value={k.value}>{k.label}</option>
        {/each}
      </select>
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="x-date">{t("feedlot_form_date")}</Label>
      <Input id="x-date" type="date" bind:value={date} disabled={saving} />
    </div>
  </div>

  <div class="flex flex-col gap-1.5">
    <Label for="x-dest">{t("feedlot_form_destination")}</Label>
    <Input id="x-dest" type="text" bind:value={destination} disabled={saving} />
  </div>

  <div class="grid grid-cols-2 gap-3">
    {#if isLot}
      <div class="flex flex-col gap-1.5">
        <Label for="x-head">{t("feedlot_form_head_count_generic")}</Label>
        <Input id="x-head" type="number" min="1" step="1" bind:value={headCount} disabled={saving} />
      </div>
    {/if}
    <div class="flex flex-col gap-1.5">
      <Label for="x-weight">{t("feedlot_form_weight")}</Label>
      <Input id="x-weight" type="number" min="0" step="0.01" bind:value={weight} disabled={saving} />
    </div>
  </div>

  {#if isSale}
    <div class="flex flex-col gap-1.5">
      <Label for="x-price">{t("feedlot_form_sale_price")}</Label>
      <Input id="x-price" type="number" min="0" step="0.0001" bind:value={salePrice} disabled={saving} />
    </div>
    {#if isOwn}
      <p class="text-sm text-muted-foreground">{t("feedlot_form_own_sale_note")}</p>
    {:else}
      <div class="flex flex-col gap-1.5">
        <Label for="x-commission">{t("feedlot_form_commission_pct")}</Label>
        <Input id="x-commission" type="number" min="0" step="0.001" bind:value={commission} disabled={saving} />
        <p class="text-xs text-muted-foreground">{t("feedlot_form_commission_hint")}</p>
      </div>
    {/if}
  {/if}

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_exit")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
