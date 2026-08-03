<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-53-api-membrane]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     API: [[API]]
     LIVE-DOC:END -->

<!--
  Create a sanitary plan (`SanitaryPlan` + its `SanitaryPlanItem`s) — a reusable,
  editable template of scheduled doses ([[adr-40-sanitary-plan-schedule]] decision 1).
  The plan holds NO dates: each item is a `HealthProduct` due `day_offset` days after
  an enrollment's start_date (decision 2) — so one plan serves many targets, each with
  its own start. Two-phase write, because `SanitaryPlanSerializer.items` is read-only:
  first `POST /api/sanitary-plans/` for the plan, then one `POST /api/sanitary-plan-items/`
  per dose. Neither posts a ledger entry — a plan is intent, billing stays with
  HealthEvent (decision 4). "＋" adds a dose line. A bare mount performs NO request
  ([[adr-22-showcase-ready-components]] rule 2), mounts with zero props and never throws
  (rule 1). Session + CSRF per [[AUTH]]. Copy Spanish, keys English ([[LOCALIZATION]]).
-->
<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { t } from "../../../i18n";

  let {
    healthProducts = [],
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    healthProducts?: Array<Record<string, any>>;
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  type DoseRow = { product: string; day_offset: string; dose: string };
  const blankDose = (): DoseRow => ({ product: "", day_offset: "0", dose: "1" });

  const activeProducts = $derived(
    healthProducts.filter((p) => (p.is_active ?? true) !== false),
  );

  let name = $state("");
  let description = $state("");
  let doses = $state<DoseRow[]>([blankDose()]);
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const filledDoses = $derived(doses.filter((d) => d.product !== ""));
  const valid = $derived(name.trim() !== "" && filledDoses.length > 0);

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  function addDose(): void {
    doses = [...doses, blankDose()];
  }
  function removeDose(i: number): void {
    doses = doses.filter((_, idx) => idx !== i);
  }

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    ok = false;
    try {
      // Phase 1 — the plan itself (name + description; items are read-only here).
      const planBody: Record<string, unknown> = { name: name.trim() };
      if (description.trim() !== "") planBody.description = description.trim();
      const planRes = await fetch(`${publicBackendUrl}/api/sanitary-plans/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": readCsrfTokenFromCookie(),
        },
        body: JSON.stringify(planBody),
      });
      if (!planRes.ok) {
        error = await readError(planRes);
        return;
      }
      const plan = await planRes.json();
      const planId = Number(plan?.id);

      // Phase 2 — one dose line per item, keyed to the new plan.
      for (const d of filledDoses) {
        const itemBody: Record<string, unknown> = {
          plan: planId,
          product: Number(d.product),
          day_offset: d.day_offset !== "" ? Number(d.day_offset) : 0,
          dose: d.dose !== "" ? Number(d.dose) : 1,
        };
        const itemRes = await fetch(`${publicBackendUrl}/api/sanitary-plan-items/`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": readCsrfTokenFromCookie(),
          },
          body: JSON.stringify(itemBody),
        });
        if (!itemRes.ok) {
          // The plan exists but a dose failed: say so honestly rather than pretend
          // the whole plan saved. The operator can add the remaining doses by editing.
          error = t("feedlot_plan_item_error").replace("{n}", name.trim());
          onsaved?.();
          return;
        }
      }
      ok = true;
      name = "";
      description = "";
      doses = [blankDose()];
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
    <Label for="plan-name">{t("feedlot_form_plan_name")}</Label>
    <Input id="plan-name" type="text" bind:value={name} disabled={saving} />
  </div>
  <div class="flex flex-col gap-1.5">
    <Label for="plan-desc">{t("feedlot_form_plan_description")}</Label>
    <Input id="plan-desc" type="text" bind:value={description} disabled={saving} />
  </div>

  <div class="flex flex-col gap-2">
    <Label>{t("feedlot_form_plan_doses")}</Label>
    {#each doses as dose, i (i)}
      <div class="grid grid-cols-[2fr_1fr_1fr_auto] items-end gap-2 rounded-md border border-border/40 p-2">
        <div class="flex flex-col gap-1.5">
          <Label for={`pd-prod-${i}`}>{t("feedlot_form_plan_dose_product")}</Label>
          <select id={`pd-prod-${i}`} class={inputClass} bind:value={dose.product} disabled={saving}>
            <option value="">{t("feedlot_form_plan_product_placeholder")}</option>
            {#each activeProducts as p (p.id)}
              <option value={String(p.id)}>{p.name}</option>
            {/each}
          </select>
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for={`pd-off-${i}`}>{t("feedlot_form_plan_dose_offset")}</Label>
          <Input id={`pd-off-${i}`} type="number" min="0" step="1" bind:value={dose.day_offset} disabled={saving} />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for={`pd-dose-${i}`}>{t("feedlot_form_plan_dose_amount")}</Label>
          <Input id={`pd-dose-${i}`} type="number" min="0" step="0.01" bind:value={dose.dose} disabled={saving} />
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={saving || doses.length === 1}
          onclick={() => removeDose(i)}
        >
          {t("feedlot_form_remove")}
        </Button>
      </div>
    {/each}
    <div>
      <Button type="button" variant="secondary" size="sm" disabled={saving} onclick={addDose}>
        {t("feedlot_form_plan_add_dose")}
      </Button>
    </div>
  </div>

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_plan")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
