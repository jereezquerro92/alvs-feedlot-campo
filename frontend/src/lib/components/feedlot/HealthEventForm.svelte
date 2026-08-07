<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-53-api-membrane]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     API: [[API]]
     LIVE-DOC:END -->

<!--
  Register a sanitary application (vaccine/treatment) for one animal OR one lot.
  Writes only through the declared endpoint `POST /api/health-events/`, which routes
  to `register_health_event`: every application ALWAYS posts a debit
  ([[adr-28-animal-lifecycle-and-sanitary]] rule 5) — this form never decides that,
  the service does; `unit_price` is snapshotted server-side from the product. A bare
  mount performs NO request ([[adr-22-showcase-ready-components]] rule 2), mounts with
  zero props and never throws (rule 1). Session + CSRF per [[AUTH]].
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
    animals = [],
    lots = [],
    healthProducts = [],
    today = "",
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    clientId?: number | null;
    animals?: Array<Record<string, any>>;
    lots?: Array<Record<string, any>>;
    healthProducts?: Array<Record<string, any>>;
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

  const products = $derived(
    healthProducts.filter((p) => (p.is_active ?? true) !== false),
  );

  let target = $state("");
  let product = $state("");
  let quantity = $state("");
  let headCount = $state("");
  let appliedBy = $state("");
  let notes = $state("");
  let date = $state(today);
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const isLot = $derived(target.startsWith("lot:"));
  const valid = $derived(
    clientId !== null &&
      target !== "" &&
      product !== "" &&
      quantity !== "" &&
      Number(quantity) > 0 &&
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
      product: Number(product),
      quantity: Number(quantity),
      date,
    };
    if (isLot && headCount !== "") body.head_count = Number(headCount);
    if (appliedBy !== "") body.applied_by = appliedBy;
    if (notes !== "") body.notes = notes;
    try {
      const res = await fetch(`${publicBackendUrl}/api/health-events/`, {
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
      headCount = "";
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
    <Label for="h-target">{t("feedlot_form_target")}</Label>
    <select id="h-target" class={inputClass} bind:value={target} disabled={saving}>
      <option value="" disabled>{t("feedlot_form_target_placeholder")}</option>
      {#each targets as opt (opt.value)}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </div>

  <div class="flex flex-col gap-1.5">
    <Label for="h-product">{t("feedlot_form_health_product")}</Label>
    <select id="h-product" class={inputClass} bind:value={product} disabled={saving}>
      <option value="" disabled>{t("feedlot_form_health_product_placeholder")}</option>
      {#each products as p (p.id)}
        <option value={String(p.id)}>{p.name}{p.unit ? ` (${p.unit})` : ""}</option>
      {/each}
    </select>
  </div>

  <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
    <div class="flex flex-col gap-1.5">
      <Label for="h-qty">{t("feedlot_form_quantity")}</Label>
      <Input id="h-qty" type="number" min="0" step="0.001" bind:value={quantity} disabled={saving} />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="h-date">{t("feedlot_form_date")}</Label>
      <DatePicker
        id="h-date"
        class="gap-0"
        bind:value={date}
        label={t("feedlot_form_date")}
        placeholder={t("feedlot_form_date_placeholder")}
        disabled={saving}
      />
    </div>
    {#if isLot}
      <div class="flex flex-col gap-1.5">
        <Label for="h-head">{t("feedlot_form_head_count_generic")}</Label>
        <Input id="h-head" type="number" min="1" step="1" bind:value={headCount} disabled={saving} />
      </div>
    {/if}
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="h-by">{t("feedlot_form_applied_by")}</Label>
      <Input id="h-by" type="text" bind:value={appliedBy} disabled={saving} />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="h-notes">{t("feedlot_form_notes")}</Label>
      <Input id="h-notes" type="text" bind:value={notes} disabled={saving} />
    </div>
  </div>

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_health")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
