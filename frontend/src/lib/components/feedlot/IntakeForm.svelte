<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Register a cattle intake for one client. Writes only through the declared endpoint
  `POST /api/intakes/`, which dispatches on `mode`
  ([[adr-26-livestock-individual-and-lot]] rule 1): `individual` creates one Animal
  per ear tag; `lot` creates an anonymous Lot carried as head_count + total_weight.
  Both modes are first-class. A bare mount performs NO request
  ([[adr-22-showcase-ready-components]] rule 2), mounts with zero props and never
  throws (rule 1). Session + CSRF per [[AUTH]].
-->
<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { t } from "../../../i18n";

  let {
    clientId = null,
    today = "",
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    clientId?: number | null;
    today?: string;
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  const categories = [
    { value: "cow", label: "Vaca" },
    { value: "bull", label: "Toro" },
    { value: "steer", label: "Novillo" },
    { value: "heifer", label: "Vaquillona" },
    { value: "calf", label: "Ternero/a" },
  ];

  type AnimalRow = { ear_tag: string; category: string; sex: string; entry_weight: string };
  const blankAnimal = (): AnimalRow => ({ ear_tag: "", category: "steer", sex: "", entry_weight: "" });

  let mode = $state("individual");
  let date = $state(today);
  let animals = $state<AnimalRow[]>([blankAnimal()]);
  let code = $state("");
  let headCount = $state("");
  let totalWeight = $state("");
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const individualValid = $derived(
    animals.length > 0 && animals.every((a) => a.ear_tag.trim() !== "" && a.category !== ""),
  );
  const lotValid = $derived(
    code.trim() !== "" && headCount !== "" && Number(headCount) > 0 && totalWeight !== "" && Number(totalWeight) > 0,
  );
  const valid = $derived(
    clientId !== null && date !== "" && (mode === "individual" ? individualValid : lotValid),
  );

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  function addAnimal(): void {
    animals = [...animals, blankAnimal()];
  }
  function removeAnimal(i: number): void {
    animals = animals.filter((_, idx) => idx !== i);
  }

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    ok = false;
    const body: Record<string, unknown> = { client: clientId, date, mode };
    if (mode === "individual") {
      body.animals = animals.map((a) => {
        const row: Record<string, unknown> = { ear_tag: a.ear_tag.trim(), category: a.category };
        if (a.sex !== "") row.sex = a.sex;
        if (a.entry_weight !== "") row.entry_weight = Number(a.entry_weight);
        return row;
      });
    } else {
      body.code = code.trim();
      body.head_count = Number(headCount);
      body.total_weight = Number(totalWeight);
    }
    try {
      const res = await fetch(`${publicBackendUrl}/api/intakes/`, {
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
      animals = [blankAnimal()];
      code = "";
      headCount = "";
      totalWeight = "";
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
      <Label for="i-mode">{t("feedlot_form_intake_mode")}</Label>
      <select id="i-mode" class={inputClass} bind:value={mode} disabled={saving}>
        <option value="individual">{t("feedlot_form_intake_mode_individual")}</option>
        <option value="lot">{t("feedlot_form_intake_mode_lot")}</option>
      </select>
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="i-date">{t("feedlot_form_date")}</Label>
      <Input id="i-date" type="date" bind:value={date} disabled={saving} />
    </div>
  </div>

  {#if mode === "individual"}
    <div class="flex flex-col gap-3">
      {#each animals as animal, i (i)}
        <div class="grid grid-cols-[1fr_1fr_auto] items-end gap-2 rounded-md border border-border/40 p-2">
          <div class="flex flex-col gap-1.5">
            <Label for={`i-tag-${i}`}>{t("feedlot_form_ear_tag")}</Label>
            <Input id={`i-tag-${i}`} type="text" bind:value={animal.ear_tag} disabled={saving} />
          </div>
          <div class="flex flex-col gap-1.5">
            <Label for={`i-cat-${i}`}>{t("feedlot_form_category")}</Label>
            <select id={`i-cat-${i}`} class={inputClass} bind:value={animal.category} disabled={saving}>
              {#each categories as c (c.value)}
                <option value={c.value}>{c.label}</option>
              {/each}
            </select>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={saving || animals.length === 1}
            onclick={() => removeAnimal(i)}
          >
            {t("feedlot_form_remove")}
          </Button>
          <div class="flex flex-col gap-1.5">
            <Label for={`i-sex-${i}`}>{t("feedlot_form_sex")}</Label>
            <select id={`i-sex-${i}`} class={inputClass} bind:value={animal.sex} disabled={saving}>
              <option value="">—</option>
              <option value="male">Macho</option>
              <option value="female">Hembra</option>
            </select>
          </div>
          <div class="flex flex-col gap-1.5">
            <Label for={`i-w-${i}`}>{t("feedlot_form_entry_weight")}</Label>
            <Input id={`i-w-${i}`} type="number" min="0" step="0.01" bind:value={animal.entry_weight} disabled={saving} />
          </div>
        </div>
      {/each}
      <div>
        <Button type="button" variant="secondary" size="sm" disabled={saving} onclick={addAnimal}>
          {t("feedlot_form_add_animal")}
        </Button>
      </div>
    </div>
  {:else}
    <div class="flex flex-col gap-1.5">
      <Label for="i-code">{t("feedlot_form_lot_code")}</Label>
      <Input id="i-code" type="text" bind:value={code} disabled={saving} />
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div class="flex flex-col gap-1.5">
        <Label for="i-head">{t("feedlot_form_lot_head_count")}</Label>
        <Input id="i-head" type="number" min="1" step="1" bind:value={headCount} disabled={saving} />
      </div>
      <div class="flex flex-col gap-1.5">
        <Label for="i-tw">{t("feedlot_form_total_weight")}</Label>
        <Input id="i-tw" type="number" min="0" step="0.01" bind:value={totalWeight} disabled={saving} />
      </div>
    </div>
  {/if}

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_intake")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
