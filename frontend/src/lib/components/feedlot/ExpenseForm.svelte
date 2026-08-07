<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-53-api-membrane]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     API: [[API]]
     LIVE-DOC:END -->

<!--
  Register an extra charge (labor / fuel / machinery / other) against a client's
  current account. Writes only through the declared endpoint `POST /api/expenses/`,
  which routes to `register_expense`: it snapshots `unit_price × quantity` and posts
  a `service` DEBIT through the generic `(source_kind, source_id)` seam
  ([[adr-24-feedlot-domain]] rule 4, [[adr-25-account-ledger]] rule 3). This is the
  field manager's "carga de deudas" via an immutable event, never a manual ledger
  debit ([[adr-44-field-operational-roles]] decision 6). The lot is optional: null
  charges the whole client. A bare mount performs NO request
  ([[adr-22-showcase-ready-components]] rule 2), mounts with zero props and never
  throws (rule 1). Session + CSRF per [[AUTH]]; copy via i18n ([[LOCALIZATION]]).
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
    lots = [],
    today = "",
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    clientId?: number | null;
    lots?: Array<Record<string, any>>;
    today?: string;
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  let category = $state("labor");
  let title = $state("");
  let lot = $state(""); // "" = whole client (null)
  let quantity = $state("");
  let unitPrice = $state("");
  let fuelKind = $state("");
  let date = $state(today);
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  // Category drives the labels: hours×price/hour, litres×price/litre, or plain
  // quantity×unit price. The backend field names are the same regardless.
  const qtyLabel = $derived(
    category === "labor"
      ? t("feedlot_expense_hours")
      : category === "fuel"
        ? t("feedlot_expense_litres")
        : t("feedlot_expense_quantity"),
  );
  const priceLabel = $derived(
    category === "labor"
      ? t("feedlot_expense_price_hour")
      : category === "fuel"
        ? t("feedlot_expense_price_litre")
        : t("feedlot_expense_price_unit"),
  );

  const total = $derived(
    quantity !== "" && unitPrice !== "" && Number(quantity) > 0 && Number(unitPrice) >= 0
      ? Number(quantity) * Number(unitPrice)
      : null,
  );

  const valid = $derived(
    clientId !== null &&
      title.trim() !== "" &&
      quantity !== "" &&
      Number(quantity) > 0 &&
      unitPrice !== "" &&
      Number(unitPrice) >= 0 &&
      date !== "",
  );

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  function fmtMoney(v: number): string {
    return v.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 2 });
  }

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    ok = false;
    const body: Record<string, unknown> = {
      client: clientId,
      date,
      title: title.trim(),
      category,
      lot: lot === "" ? null : Number(lot),
      unit_price: Number(unitPrice),
      quantity: Number(quantity),
    };
    if (category === "fuel" && fuelKind.trim() !== "") {
      body.fuel_kind = fuelKind.trim();
    }
    try {
      const res = await fetch(`${publicBackendUrl}/api/expenses/`, {
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
      title = "";
      quantity = "";
      unitPrice = "";
      fuelKind = "";
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
    <Label for="ex-category">{t("feedlot_expense_category")}</Label>
    <select id="ex-category" class={inputClass} bind:value={category} disabled={saving}>
      <option value="labor">{t("feedlot_expense_cat_labor")}</option>
      <option value="fuel">{t("feedlot_expense_cat_fuel")}</option>
      <option value="machinery">{t("feedlot_expense_cat_machinery")}</option>
      <option value="other">{t("feedlot_expense_cat_other")}</option>
    </select>
  </div>

  <div class="flex flex-col gap-1.5">
    <Label for="ex-title">{t("feedlot_expense_title")}</Label>
    <Input id="ex-title" type="text" bind:value={title} disabled={saving}
      placeholder={t("feedlot_expense_title_placeholder")} />
  </div>

  <div class="flex flex-col gap-1.5">
    <Label for="ex-lot">{t("feedlot_expense_lot")}</Label>
    <select id="ex-lot" class={inputClass} bind:value={lot} disabled={saving}>
      <option value="">{t("feedlot_expense_lot_all")}</option>
      {#each lots as l (l.id)}
        <option value={String(l.id)}>{l.code ?? `#${l.id}`}</option>
      {/each}
    </select>
    <p class="text-xs text-muted-foreground">{t("feedlot_expense_lot_hint")}</p>
  </div>

  {#if category === "fuel"}
    <div class="flex flex-col gap-1.5">
      <Label for="ex-fuelkind">{t("feedlot_expense_fuel_kind")}</Label>
      <Input id="ex-fuelkind" type="text" bind:value={fuelKind} disabled={saving}
        placeholder={t("feedlot_expense_fuel_kind_placeholder")} />
    </div>
  {/if}

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="ex-qty">{qtyLabel}</Label>
      <Input id="ex-qty" type="number" min="0" step="0.01" bind:value={quantity} disabled={saving} />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="ex-price">{priceLabel}</Label>
      <Input id="ex-price" type="number" min="0" step="0.01" bind:value={unitPrice} disabled={saving} />
    </div>
  </div>

  <div class="flex flex-col gap-1.5">
    <Label for="ex-date">{t("feedlot_form_date")}</Label>
      <DatePicker
        id="ex-date"
        class="gap-0"
        bind:value={date}
        label={t("feedlot_form_date")}
        placeholder={t("feedlot_form_date_placeholder")}
        disabled={saving}
      />
    </div>

  {#if total !== null}
    <div class="rounded-md px-3 py-2 text-sm" style="background: var(--muted);">
      {t("feedlot_expense_total_preview")} <span class="font-semibold tabular-nums">{fmtMoney(total)}</span>
    </div>
  {/if}

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_expense_save")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if clientId === null}
    <p class="text-sm text-muted-foreground">{t("feedlot_expense_pick_client")}</p>
  {/if}
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
