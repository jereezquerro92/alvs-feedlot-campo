<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-53-api-membrane]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     API: [[API]]
     LIVE-DOC:END -->

<!--
  Create a ración (`Ration` + `RationLine`s) — the recipe: which `FeedType`, in what
  proportion, at what dry-matter percent ([[adr-33-feedyard-operating-loop]] decision
  4). It is an editable catalog (decision 5), not a costed item: the ración has no
  price of its own — the cost appears only when it is served as a `FeedingEvent` with
  the day's historical unit_price ([[adr-25-account-ledger]] rule 3). Writes only
  through the declared endpoint `POST /api/rations/` ([[API]]), which creates the
  Ration then its nested lines. This form exists because the loading-order form needs
  raciones to choose from (task #21). "＋" adds a feed line. A bare mount performs NO
  request ([[adr-22-showcase-ready-components]] rule 2), mounts with zero props and
  never throws (rule 1). Session + CSRF per [[AUTH]].
-->
<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { t } from "../../../i18n";

  let {
    feedTypes = [],
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    feedTypes?: Array<Record<string, any>>;
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  type LineRow = { feed_type: string; proportion: string; dry_matter_pct: string };
  const blankLine = (): LineRow => ({ feed_type: "", proportion: "", dry_matter_pct: "" });

  let name = $state("");
  let description = $state("");
  let lines = $state<LineRow[]>([blankLine()]);
  let saving = $state(false);
  let error = $state("");
  let ok = $state(false);

  const filledLines = $derived(lines.filter((l) => l.feed_type !== ""));
  const valid = $derived(name.trim() !== "" && filledLines.length > 0);

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  function addLine(): void {
    lines = [...lines, blankLine()];
  }
  function removeLine(i: number): void {
    lines = lines.filter((_, idx) => idx !== i);
  }

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    ok = false;
    const body: Record<string, unknown> = {
      name: name.trim(),
      lines: filledLines.map((l) => {
        const row: Record<string, unknown> = { feed_type: Number(l.feed_type) };
        row.proportion = l.proportion !== "" ? Number(l.proportion) : 0;
        if (l.dry_matter_pct !== "") row.dry_matter_pct = Number(l.dry_matter_pct);
        return row;
      }),
    };
    if (description.trim() !== "") body.description = description.trim();
    try {
      const res = await fetch(`${publicBackendUrl}/api/rations/`, {
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
      name = "";
      description = "";
      lines = [blankLine()];
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
    <Label for="ration-name">{t("feedlot_form_ration_name")}</Label>
    <Input id="ration-name" type="text" bind:value={name} disabled={saving} />
  </div>
  <div class="flex flex-col gap-1.5">
    <Label for="ration-desc">{t("feedlot_form_ration_description")}</Label>
    <Input id="ration-desc" type="text" bind:value={description} disabled={saving} />
  </div>

  <div class="flex flex-col gap-2">
    <Label>{t("feedlot_form_ration_lines")}</Label>
    {#each lines as line, i (i)}
      <div class="grid grid-cols-[2fr_1fr_1fr_auto] items-end gap-2 rounded-md border border-border/40 p-2">
        <div class="flex flex-col gap-1.5">
          <Label for={`rl-feed-${i}`}>{t("feedlot_form_ration_line_feed")}</Label>
          <select id={`rl-feed-${i}`} class={inputClass} bind:value={line.feed_type} disabled={saving}>
            <option value="">{t("feedlot_form_feed_type_placeholder")}</option>
            {#each feedTypes as ft (ft.id)}
              <option value={String(ft.id)}>{ft.name}</option>
            {/each}
          </select>
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for={`rl-prop-${i}`}>{t("feedlot_form_ration_line_proportion")}</Label>
          <Input id={`rl-prop-${i}`} type="number" min="0" step="0.01" bind:value={line.proportion} disabled={saving} />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for={`rl-dm-${i}`}>{t("feedlot_form_ration_line_dm")}</Label>
          <Input id={`rl-dm-${i}`} type="number" min="0" step="0.01" bind:value={line.dry_matter_pct} disabled={saving} />
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={saving || lines.length === 1}
          onclick={() => removeLine(i)}
        >
          {t("feedlot_form_remove")}
        </Button>
      </div>
    {/each}
    <div>
      <Button type="button" variant="secondary" size="sm" disabled={saving} onclick={addLine}>
        {t("feedlot_form_ration_add_line")}
      </Button>
    </div>
  </div>

  <div class="flex items-center gap-3">
    <Button type="submit" disabled={!valid || saving}>{t("feedlot_form_save_ration")}</Button>
    {#if ok}<span class="text-sm text-success">{t("feedlot_form_saved")}</span>{/if}
  </div>
  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
</form>
