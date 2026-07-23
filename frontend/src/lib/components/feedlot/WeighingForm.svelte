<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Register a weighing for one animal OR one lot ([[adr-26-livestock-individual-and-lot]]
  rule 3 — exactly one target). Writes only through the declared endpoint
  `POST /api/weighings/`, which routes to the domain service (never a raw write).
  A bare mount performs NO request ([[adr-22-showcase-ready-components]] rule 2):
  the POST fires only on explicit submit. Mounts with zero props and never throws
  (rule 1). Session + CSRF per the app's write pattern ([[AUTH]], [[FRONTEND]]).
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
    /** Server-supplied YYYY-MM-DD default, so the field is filled without a
     * client clock; the caller owns "today" ([[adr-22-showcase-ready-components]]). */
    today?: string;
    publicBackendUrl?: string;
    /** Safe no-op default (adr-22 rule 2): a bare mount wires no side effect. */
    onsaved?: (() => void) | undefined;
  } = $props();

  const targets = $derived([
    ...lots
      .filter((l) => (l.status ?? "active") === "active")
      .map((l) => ({ value: `lot:${l.id}`, label: `${t("feedlot_form_lot")} ${l.code ?? l.id}`, isLot: true })),
    ...animals
      .filter((a) => (a.status ?? "active") === "active")
      .map((a) => ({ value: `animal:${a.id}`, label: a.ear_tag ?? `#${a.id}`, isLot: false })),
  ]);

  let target = $state("");
  let weight = $state("");
  let headCount = $state("");
  let method = $state("scale");
  let date = $state(today);
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const isLot = $derived(target.startsWith("lot:"));
  const valid = $derived(target !== "" && weight !== "" && Number(weight) > 0 && date !== "");

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
      ...parseTarget(target),
      date,
      weight: Number(weight),
      method,
    };
    if (isLot && headCount !== "") body.head_count = Number(headCount);
    try {
      const res = await fetch(`${publicBackendUrl}/api/weighings/`, {
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
      weight = "";
      headCount = "";
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
    <Label for="w-target">{t("feedlot_form_target")}</Label>
    <select id="w-target" class={inputClass} bind:value={target} disabled={saving}>
      <option value="" disabled>{t("feedlot_form_target_placeholder")}</option>
      {#each targets as opt (opt.value)}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </div>

  <div class="grid grid-cols-2 gap-3">
    <div class="flex flex-col gap-1.5">
      <Label for="w-weight">{t("feedlot_form_weight")}</Label>
      <Input id="w-weight" type="number" min="0" step="0.01" bind:value={weight} disabled={saving} />
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="w-date">{t("feedlot_form_date")}</Label>
      <Input id="w-date" type="date" bind:value={date} disabled={saving} />
    </div>
  </div>

  {#if isLot}
    <div class="flex flex-col gap-1.5">
      <Label for="w-head">{t("feedlot_form_head_count")}</Label>
      <Input id="w-head" type="number" min="1" step="1" bind:value={headCount} disabled={saving} />
      <span class="text-xs text-muted-foreground">{t("feedlot_form_head_count_hint")}</span>
    </div>
  {/if}

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_weighing")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
