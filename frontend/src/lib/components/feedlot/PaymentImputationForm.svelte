<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Impute a client's payment against its outstanding charges
  ([[adr-41-payment-allocation]]). Writes only through the declared endpoint
  `POST /api/payment-allocations/`, which routes to `impute_payment`: it creates
  `PaymentAllocation` rows and posts NO ledger entry and moves NO balance — the
  credit already moved the balance when the payment posted (adr-41 decision 1).
  Two modes: automatic FIFO oldest-charge-first (`auto=true`, decision 3), or an
  explicit `{entry, amount}` line. A bare mount performs NO request
  ([[adr-22-showcase-ready-components]] rule 2), mounts with zero props and never
  throws (rule 1). Session + CSRF per [[AUTH]]. Copy Spanish, keys English
  ([[LOCALIZATION]]).
-->
<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { t } from "../../../i18n";

  type Payment = { id: number; date?: string; amount?: string | number | null };
  type Allocation = { payment?: number; amount?: string | number | null };
  type Charge = {
    entry: number;
    date?: string;
    concept?: string;
    outstanding?: string | number | null;
  };

  let {
    clientId = null,
    payments = [],
    allocations = [],
    charges = [],
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    clientId?: number | null;
    payments?: Payment[];
    allocations?: Allocation[];
    charges?: Charge[];
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  let paymentId = $state("");
  let auto = $state(true);
  let entryId = $state("");
  let amount = $state("");
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const CONCEPTS: Record<string, string> = {
    feeding: "Alimentación",
    health: "Sanidad",
    service: "Servicio",
    adjustment: "Ajuste",
    payment: "Pago",
  };

  function num(v: unknown): number {
    if (v === null || v === undefined || v === "") return 0;
    const n = Number(v);
    return Number.isNaN(n) ? 0 : n;
  }

  // Remaining unallocated per payment = amount − Σ its allocations (adr-41 dec 2).
  const remainingByPayment = $derived.by(() => {
    const alloc: Record<number, number> = {};
    for (const a of allocations) {
      if (a.payment == null) continue;
      alloc[a.payment] = (alloc[a.payment] ?? 0) + num(a.amount);
    }
    const out: Record<number, number> = {};
    for (const p of payments) out[p.id] = num(p.amount) - (alloc[p.id] ?? 0);
    return out;
  });

  const openPayments = $derived(payments.filter((p) => (remainingByPayment[p.id] ?? 0) > 0));
  const openCharges = $derived(charges.filter((c) => num(c.outstanding) > 0));

  const valid = $derived(
    clientId !== null &&
      paymentId !== "" &&
      (auto || (entryId !== "" && amount !== "" && Number(amount) > 0)),
  );

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    ok = false;
    const body: Record<string, unknown> = { payment: Number(paymentId) };
    if (auto) {
      body.auto = true;
    } else {
      body.allocations = [{ entry: Number(entryId), amount: Number(amount) }];
    }
    try {
      const res = await fetch(`${publicBackendUrl}/api/payment-allocations/`, {
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
      amount = "";
      entryId = "";
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
    <Label for="pa-payment">{t("feedlot_impute_payment")}</Label>
    <select id="pa-payment" class={inputClass} bind:value={paymentId} disabled={saving}>
      <option value="" disabled>{t("feedlot_impute_payment_placeholder")}</option>
      {#each openPayments as p (p.id)}
        <option value={String(p.id)}>
          {p.date ?? "—"} · {formatNumber(remainingByPayment[p.id] ?? 0, "ARS")}
        </option>
      {/each}
    </select>
    {#if openPayments.length === 0}
      <p class="text-xs text-muted-foreground">{t("feedlot_impute_no_payments")}</p>
    {/if}
  </div>

  <label class="flex items-center gap-2 text-sm">
    <input type="checkbox" bind:checked={auto} disabled={saving} />
    {t("feedlot_impute_auto")}
  </label>

  {#if !auto}
    <div class="grid grid-cols-2 gap-3">
      <div class="flex flex-col gap-1.5">
        <Label for="pa-entry">{t("feedlot_impute_charge")}</Label>
        <select id="pa-entry" class={inputClass} bind:value={entryId} disabled={saving}>
          <option value="" disabled>{t("feedlot_impute_charge_placeholder")}</option>
          {#each openCharges as c (c.entry)}
            <option value={String(c.entry)}>
              {c.date ?? "—"} · {CONCEPTS[String(c.concept)] ?? c.concept} · {formatNumber(num(c.outstanding), "ARS")}
            </option>
          {/each}
        </select>
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="pa-amount">{t("feedlot_impute_amount")}</Label>
        <Input id="pa-amount" type="number" min="0" step="0.01" bind:value={amount} disabled={saving} />
      </div>
    </div>
  {/if}

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_impute_save")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
