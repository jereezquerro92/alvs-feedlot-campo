<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-53-api-membrane]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     API: [[API]]
     LIVE-DOC:END -->

<!--
  Serve a ración: the easy multi-target feeding form (tasks #21/#22). Pick one OR
  more clients, one OR more destination lots, add one OR more feeds — each feed
  carries its own ORIGEN (`own_stock` = estancia / `client_stock` = stock del
  cliente), and optionally a day-range so the same ración is loaded across several
  days. It writes ONLY `FeedingEvent`s through the declared endpoint
  `POST /api/feedings/` — one event per (lot × feed × day). The origin decides the
  charge in the backend: `own_stock` posts a debit, `client_stock` posts only the
  stock-out and no charge ([[adr-25-account-ledger]] rule 4); this form never decides
  that, it reports the fact. Nothing here writes to the ledger directly and no
  `LoadingOrder` is posted — this is executed feeding, not a plan (adr-33 decision 2).
  A per-head toggle multiplies the quantity by each lot's head count so 100 vs 120
  head differ, as the operator asked. A bare mount performs NO request
  ([[adr-22-showcase-ready-components]] rule 2), mounts with zero props and never
  throws (rule 1). Session + CSRF per [[AUTH]].
-->
<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { DatePicker } from "$lib/components/form";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { t } from "../../../i18n";

  type Client = { id: number | string; name?: string };
  type Lot = { id: number | string; client?: number | string; code?: string; head_count?: number; status?: string };
  type FeedType = { id: number | string; name?: string; unit?: string };

  let {
    clients = [],
    lots = [],
    feedTypes = [],
    today = "",
    publicBackendUrl = "",
    onsaved = undefined,
  }: {
    clients?: Client[];
    lots?: Lot[];
    feedTypes?: FeedType[];
    today?: string;
    publicBackendUrl?: string;
    onsaved?: (() => void) | undefined;
  } = $props();

  // --- selection state -------------------------------------------------------
  let selectedClients = $state<Set<string>>(new Set());
  let selectedLots = $state<Set<string>>(new Set());
  let quantityMode = $state<"per_lot" | "per_head">("per_lot");

  // Day range: single day by default, toggle to a [from, to] inclusive range.
  let dayMode = $state<"single" | "range">("single");
  let date = $state(today);
  let dateFrom = $state(today);
  let dateTo = $state(today);

  type FeedRow = { feed_type: string; quantity: string; unit_price: string; origin: string };
  const blankFeed = (): FeedRow => ({ feed_type: "", quantity: "", unit_price: "", origin: "own_stock" });
  let feeds = $state<FeedRow[]>([blankFeed()]);

  let saving = $state(false);
  let error = $state("");
  let summary = $state("");

  const clientName = (id: number | string): string =>
    clients.find((c) => String(c.id) === String(id))?.name ?? `#${id}`;

  // Lots offered = active lots of the selected clients. Picking clients narrows
  // the destination list so the operator never mixes the wrong lot in.
  const offeredLots = $derived(
    lots.filter(
      (l) =>
        (l.status ?? "active") === "active" &&
        (selectedClients.size === 0 || selectedClients.has(String(l.client))),
    ),
  );

  const filledFeeds = $derived(
    feeds.filter((f) => f.feed_type !== "" && f.quantity !== "" && Number(f.quantity) > 0 && f.unit_price !== ""),
  );

  const dates = $derived(buildDates());
  const chosenLots = $derived(offeredLots.filter((l) => selectedLots.has(String(l.id))));
  const plannedCount = $derived(chosenLots.length * filledFeeds.length * dates.length);

  const valid = $derived(
    chosenLots.length > 0 && filledFeeds.length > 0 && dates.length > 0 && !dates.includes("__invalid__"),
  );

  const inputClass =
    "flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring";

  function buildDates(): string[] {
    if (dayMode === "single") return date !== "" ? [date] : [];
    if (dateFrom === "" || dateTo === "") return [];
    const start = new Date(dateFrom + "T00:00:00");
    const end = new Date(dateTo + "T00:00:00");
    if (isNaN(start.getTime()) || isNaN(end.getTime()) || end < start) return ["__invalid__"];
    const out: string[] = [];
    const cur = new Date(start);
    // Cap at 92 days so a slipped year can't fan out into thousands of requests.
    for (let i = 0; i < 92 && cur <= end; i++) {
      out.push(cur.toISOString().slice(0, 10));
      cur.setDate(cur.getDate() + 1);
    }
    return out;
  }

  function toggle(set: Set<string>, key: string): Set<string> {
    const next = new Set(set);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    return next;
  }

  function toggleClient(id: string): void {
    selectedClients = toggle(selectedClients, id);
    // Drop any chosen lot that no longer belongs to a selected client.
    const stillOffered = new Set(
      lots
        .filter((l) => selectedClients.size === 0 || selectedClients.has(String(l.client)))
        .map((l) => String(l.id)),
    );
    selectedLots = new Set([...selectedLots].filter((k) => stillOffered.has(k)));
  }
  function toggleLot(id: string): void {
    selectedLots = toggle(selectedLots, id);
  }

  function addFeed(): void {
    feeds = [...feeds, blankFeed()];
  }
  function removeFeed(i: number): void {
    feeds = feeds.filter((_, idx) => idx !== i);
  }

  async function submit(event: Event): Promise<void> {
    event.preventDefault();
    if (!valid || saving) return;
    saving = true;
    error = "";
    summary = "";

    const csrf = readCsrfTokenFromCookie();
    let okCount = 0;
    const failures: string[] = [];

    for (const lot of chosenLots) {
      const head = Number(lot.head_count ?? 0) || 0;
      for (const feed of filledFeeds) {
        const base = Number(feed.quantity);
        const qty = quantityMode === "per_head" && head > 0 ? base * head : base;
        for (const d of dates) {
          const body = {
            client: Number(lot.client),
            lot: Number(lot.id),
            feed_type: Number(feed.feed_type),
            quantity: qty,
            unit_price: Number(feed.unit_price),
            origin: feed.origin,
            date: d,
          };
          try {
            const res = await fetch(`${publicBackendUrl}/api/feedings/`, {
              method: "POST",
              credentials: "include",
              headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
              body: JSON.stringify(body),
            });
            if (res.ok) okCount++;
            else failures.push(`${lot.code ?? lot.id} · ${d}: ${await readError(res)}`);
          } catch {
            failures.push(`${lot.code ?? lot.id} · ${d}: ${t("feedlot_form_error")}`);
          }
        }
      }
    }

    saving = false;
    if (failures.length === 0) {
      summary = t("feedlot_racion_done").replace("{n}", String(okCount));
      onsaved?.();
    } else {
      summary = t("feedlot_racion_partial")
        .replace("{ok}", String(okCount))
        .replace("{fail}", String(failures.length));
      error = failures.slice(0, 5).join(" · ");
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

<form class="flex flex-col gap-5" onsubmit={submit}>
  <!-- 1) Clients -->
  <div class="flex flex-col gap-2">
    <Label>{t("feedlot_racion_clients")}</Label>
    {#if clients.length === 0}
      <p class="text-sm text-muted-foreground">{t("feedlot_racion_no_clients")}</p>
    {:else}
      <div class="flex flex-wrap gap-2">
        {#each clients as c (c.id)}
          <button
            type="button"
            class="rounded-full border px-3 py-1 text-sm transition"
            style={selectedClients.has(String(c.id))
              ? "background: var(--primary); color: var(--primary-foreground); border-color: var(--primary);"
              : "background: var(--card); border-color: var(--border);"}
            disabled={saving}
            onclick={() => toggleClient(String(c.id))}
          >
            {c.name ?? `#${c.id}`}
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <!-- 2) Destination lots -->
  <div class="flex flex-col gap-2">
    <Label>{t("feedlot_racion_lots")}</Label>
    {#if offeredLots.length === 0}
      <p class="text-sm text-muted-foreground">{t("feedlot_racion_no_lots")}</p>
    {:else}
      <div class="flex flex-wrap gap-2">
        {#each offeredLots as l (l.id)}
          <button
            type="button"
            class="rounded-full border px-3 py-1 text-sm transition"
            style={selectedLots.has(String(l.id))
              ? "background: var(--primary); color: var(--primary-foreground); border-color: var(--primary);"
              : "background: var(--card); border-color: var(--border);"}
            disabled={saving}
            onclick={() => toggleLot(String(l.id))}
          >
            {l.code ?? `#${l.id}`} · {l.head_count ?? 0} cab. · {clientName(l.client ?? "")}
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <!-- 3) Feeds (＋) -->
  <div class="flex flex-col gap-2">
    <Label>{t("feedlot_racion_feeds")}</Label>
    {#each feeds as feed, i (i)}
      <div class="grid grid-cols-[2fr_1fr_1fr_1.4fr_auto] items-end gap-2 rounded-md border border-border/40 p-2">
        <div class="flex flex-col gap-1.5">
          <Label for={`sf-feed-${i}`}>{t("feedlot_form_feed_type")}</Label>
          <select id={`sf-feed-${i}`} class={inputClass} bind:value={feed.feed_type} disabled={saving}>
            <option value="">{t("feedlot_form_feed_type_placeholder")}</option>
            {#each feedTypes as ft (ft.id)}
              <option value={String(ft.id)}>{ft.name}</option>
            {/each}
          </select>
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for={`sf-qty-${i}`}>{t("feedlot_form_quantity")}</Label>
          <Input id={`sf-qty-${i}`} type="number" min="0" step="0.01" bind:value={feed.quantity} disabled={saving} />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for={`sf-price-${i}`}>{t("feedlot_form_unit_price")}</Label>
          <Input id={`sf-price-${i}`} type="number" min="0" step="0.01" bind:value={feed.unit_price} disabled={saving} />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for={`sf-origin-${i}`}>{t("feedlot_form_origin")}</Label>
          <select id={`sf-origin-${i}`} class={inputClass} bind:value={feed.origin} disabled={saving}>
            <option value="own_stock">{t("feedlot_form_origin_own")}</option>
            <option value="client_stock">{t("feedlot_form_origin_client")}</option>
          </select>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={saving || feeds.length === 1}
          onclick={() => removeFeed(i)}
        >
          {t("feedlot_form_remove")}
        </Button>
      </div>
    {/each}
    <div>
      <Button type="button" variant="secondary" size="sm" disabled={saving} onclick={addFeed}>
        {t("feedlot_racion_add_feed")}
      </Button>
    </div>
  </div>

  <!-- 4) Quantity mode + day range -->
  <div class="grid gap-3 sm:grid-cols-2">
    <div class="flex flex-col gap-1.5">
      <Label for="sf-qmode">{t("feedlot_racion_qty_mode")}</Label>
      <select id="sf-qmode" class={inputClass} bind:value={quantityMode} disabled={saving}>
        <option value="per_lot">{t("feedlot_racion_qty_per_lot")}</option>
        <option value="per_head">{t("feedlot_racion_qty_per_head")}</option>
      </select>
      <p class="text-xs text-muted-foreground">
        {quantityMode === "per_head" ? t("feedlot_racion_qty_per_head_hint") : t("feedlot_racion_qty_per_lot_hint")}
      </p>
    </div>
    <div class="flex flex-col gap-1.5">
      <Label for="sf-range">{t("feedlot_racion_day_mode")}</Label>
      <select id="sf-range" class={inputClass} bind:value={dayMode} disabled={saving}>
        <option value="single">{t("feedlot_racion_single_day")}</option>
        <option value="range">{t("feedlot_racion_day_range")}</option>
      </select>
    </div>
  </div>

  {#if dayMode === "single"}
    <div class="flex w-full max-w-[11rem] flex-col gap-1.5">
      <Label for="sf-date">{t("feedlot_form_date")}</Label>
      <DatePicker
        id="sf-date"
        class="gap-0"
        bind:value={date}
        label={t("feedlot_form_date")}
        placeholder={t("feedlot_form_date_placeholder")}
        disabled={saving}
      />
    </div>
  {:else}
    <div class="grid max-w-sm gap-3 sm:grid-cols-2">
      <div class="flex max-w-[11rem] flex-col gap-1.5">
        <Label for="sf-from">{t("feedlot_racion_date_from")}</Label>
        <DatePicker
          id="sf-from"
          class="gap-0"
          bind:value={dateFrom}
          label={t("feedlot_racion_date_from")}
          placeholder={t("feedlot_form_date_placeholder")}
          disabled={saving}
        />
      </div>
      <div class="flex max-w-[11rem] flex-col gap-1.5">
        <Label for="sf-to">{t("feedlot_racion_date_to")}</Label>
        <DatePicker
          id="sf-to"
          class="gap-0"
          bind:value={dateTo}
          label={t("feedlot_racion_date_to")}
          placeholder={t("feedlot_form_date_placeholder")}
          disabled={saving}
        />
      </div>
    </div>
  {/if}

  <!-- Plan preview + submit -->
  <div class="flex flex-col gap-2 rounded-lg p-3" style="background: var(--muted);">
    <p class="text-sm">
      {t("feedlot_racion_preview")
        .replace("{lots}", String(chosenLots.length))
        .replace("{feeds}", String(filledFeeds.length))
        .replace("{days}", String(dates.includes("__invalid__") ? 0 : dates.length))
        .replace("{n}", String(dates.includes("__invalid__") ? 0 : plannedCount))}
    </p>
    <div class="flex items-center gap-3">
      <Button type="submit" disabled={!valid || saving}>
        {saving ? t("feedlot_racion_saving") : t("feedlot_racion_save")}
      </Button>
      {#if summary}<span class="text-sm text-success">{summary}</span>{/if}
    </div>
    {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
  </div>
</form>
