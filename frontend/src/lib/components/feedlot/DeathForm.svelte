<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Register a death for one animal OR one lot ([[adr-26-livestock-individual-and-lot]]
  rule 3 — exactly one target). Writes only through the declared endpoint
  `POST /api/deaths/`, which routes to the domain service (never a raw write).
  A death posts NO ledger entry ([[adr-28-animal-lifecycle-and-sanitary]] rule 3);
  this form never decides that, it only reports the fact. A bare mount performs NO
  request ([[adr-22-showcase-ready-components]] rule 2), mounts with zero props and
  never throws (rule 1). Session + CSRF per the app's write pattern ([[AUTH]]).
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
    today = "",
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    animals?: Array<Record<string, any>>;
    lots?: Array<Record<string, any>>;
    today?: string;
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  const causes = [
    { value: "disease", label: "Enfermedad" },
    { value: "accident", label: "Accidente" },
    { value: "unknown", label: "Desconocida" },
    { value: "other", label: "Otra" },
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
  let cause = $state("unknown");
  let causeDetail = $state("");
  let headCount = $state("");
  let weight = $state("");
  let date = $state(today);
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const isLot = $derived(target.startsWith("lot:"));
  const valid = $derived(target !== "" && date !== "");

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
    const body: Record<string, unknown> = { ...parseTarget(target), date, cause };
    if (causeDetail !== "") body.cause_detail = causeDetail;
    if (isLot && headCount !== "") body.head_count = Number(headCount);
    if (weight !== "") body.weight = Number(weight);
    try {
      const res = await fetch(`${publicBackendUrl}/api/deaths/`, {
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
      causeDetail = "";
      headCount = "";
      weight = "";
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
    <Label for="d-target">{t("feedlot_form_target")}</Label>
    <select id="d-target" class={inputClass} bind:value={target} disabled={saving}>
      <option value="" disabled>{t("feedlot_form_target_placeholder")}</option>
      {#each targets as opt (opt.value)}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="d-cause">{t("feedlot_form_cause")}</Label>
      <select id="d-cause" class={inputClass} bind:value={cause} disabled={saving}>
        {#each causes as c (c.value)}
          <option value={c.value}>{c.label}</option>
        {/each}
      </select>
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="d-date">{t("feedlot_form_date")}</Label>
      <Input id="d-date" type="date" bind:value={date} disabled={saving} />
    </div>
  </div>

  <div class="flex flex-col gap-1.5">
    <Label for="d-detail">{t("feedlot_form_cause_detail")}</Label>
    <Input id="d-detail" type="text" bind:value={causeDetail} disabled={saving} />
  </div>

  <div class="grid grid-cols-2 gap-3">
    {#if isLot}
      <div class="flex flex-col gap-1.5">
        <Label for="d-head">{t("feedlot_form_head_count_generic")}</Label>
        <Input id="d-head" type="number" min="1" step="1" bind:value={headCount} disabled={saving} />
      </div>
    {/if}
    <div class="flex flex-col gap-1.5">
      <Label for="d-weight">{t("feedlot_form_weight")}</Label>
      <Input id="d-weight" type="number" min="0" step="0.01" bind:value={weight} disabled={saving} />
    </div>
  </div>

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_death")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
