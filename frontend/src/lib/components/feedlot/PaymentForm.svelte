<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Register a client payment ([[adr-25-account-ledger]] rule 7). Writes only through
  the declared endpoint `POST /api/payments/`, which routes to `register_payment`:
  it posts a `credit` `LedgerEntry` that reduces the balance. The amount is NOT
  capped at the outstanding debt — a payment larger than what the client owes is
  legitimate and leaves a credit balance ("saldo a favor"): positive balance = the
  client owes, negative = the feedlot owes the client (adr-25 rule 2). Imputation
  against specific charges is a separate, optional step (adr-41,
  PaymentImputationForm). A bare mount performs NO request
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

  let {
    accountId = null,
    balance = null,
    today = "",
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    accountId?: number | null;
    balance?: number | null;
    today?: string;
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  let amount = $state("");
  let date = $state(today);
  let method = $state("transfer");
  let reference = $state("");
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  $effect(() => {
    if (date === "" && today !== "") date = today;
  });

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  const amountNum = $derived(amount === "" ? 0 : Number(amount));
  const valid = $derived(
    accountId !== null && date !== "" && amount !== "" && amountNum > 0,
  );

  // What the balance becomes after this payment (credit lowers it; negative = saldo
  // a favor). Only a preview — the backend derives the real balance (adr-25 rule 2).
  const projected = $derived(balance === null ? null : balance - amountNum);
  const leavesFavor = $derived(projected !== null && projected < 0);

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    ok = false;
    const body: Record<string, unknown> = {
      account: Number(accountId),
      amount: Number(amount),
      date,
      method,
    };
    if (reference.trim() !== "") body.reference = reference.trim();
    try {
      const res = await fetch(`${publicBackendUrl}/api/payments/`, {
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
      reference = "";
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
      <Label for="pay-amount">{t("feedlot_payment_amount")}</Label>
      <Input id="pay-amount" type="number" min="0" step="0.01" bind:value={amount} disabled={saving} />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="pay-date">{t("feedlot_payment_date")}</Label>
      <Input id="pay-date" type="date" bind:value={date} disabled={saving} />
    </div>
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="pay-method">{t("feedlot_payment_method")}</Label>
      <select id="pay-method" class={inputClass} bind:value={method} disabled={saving}>
        <option value="transfer">{t("feedlot_payment_method_transfer")}</option>
        <option value="cash">{t("feedlot_payment_method_cash")}</option>
        <option value="check">{t("feedlot_payment_method_check")}</option>
        <option value="other">{t("feedlot_payment_method_other")}</option>
      </select>
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="pay-reference">{t("feedlot_payment_reference")}</Label>
      <Input id="pay-reference" type="text" bind:value={reference} disabled={saving} />
    </div>
  </div>

  {#if leavesFavor && projected !== null}
    <p class="text-xs text-muted-foreground">
      {t("feedlot_payment_favor_hint").replace("{n}", formatNumber(Math.abs(projected), "ARS"))}
    </p>
  {/if}

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_payment_save")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
