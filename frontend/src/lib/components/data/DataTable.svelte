<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts" module>
  export type DataColumn = {
    key: string;
    label: string;
    align?: "left" | "right";
    /** Render this column's value through NumericValue. */
    numeric?: boolean;
    /** Optional currency label passed to NumericValue for numeric columns. */
    currency?: string;
    /** Allow click-to-sort on this column's header. */
    sortable?: boolean;
    /** Render this column's value as a locale-formatted date. */
    date?: boolean;
    /** Fixed column width (any CSS width) — the table is table-fixed (#167). */
    width?: string;
  };

  export type DataRow = Record<string, unknown>;
</script>

<script lang="ts">
  import * as Table from "$lib/components/ui/table";
  import { Button } from "$lib/components/ui/button";
  import NumericValue from "./NumericValue.svelte";
  import { cn } from "$lib/utils";
  import { defaultLocale } from "../../../i18n/config";
  import type { Snippet } from "svelte";

  const dateFormat = new Intl.DateTimeFormat(defaultLocale, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  function formatDate(value: unknown): string {
    const parsed = new Date(String(value));
    return Number.isNaN(parsed.getTime()) ? String(value ?? "") : dateFormat.format(parsed);
  }

  let {
    columns = [],
    rows = [],
    getRowKey = (row: DataRow, i: number) => String(row.id ?? i),
    detail = undefined,
    class: className = undefined,
  }: {
    columns?: DataColumn[];
    rows?: DataRow[];
    getRowKey?: (row: DataRow, index: number) => string;
    /** Rendered in a full-width panel below a row when it is expanded. */
    detail?: Snippet<[DataRow]>;
    class?: string;
  } = $props();

  let expanded = $state<string | null>(null);
  let sortKey = $state<string | null>(null);
  let sortDir = $state<"asc" | "desc">("asc");

  function toggleSort(col: DataColumn): void {
    if (!col.sortable) return;
    if (sortKey === col.key) {
      sortDir = sortDir === "asc" ? "desc" : "asc";
    } else {
      sortKey = col.key;
      sortDir = "asc";
    }
  }

  function toggleRow(key: string): void {
    if (!detail) return;
    expanded = expanded === key ? null : key;
  }

  const sortedRows = $derived.by(() => {
    if (!sortKey) return rows;
    const key = sortKey;
    const dir = sortDir === "asc" ? 1 : -1;
    return [...rows].sort((a, b) => {
      const av = a[key];
      const bv = b[key];
      if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir;
      return String(av ?? "").localeCompare(String(bv ?? "")) * dir;
    });
  });
</script>

<div class="scrim">
<Table.Root class={className}>
  <Table.Header>
    <Table.Row>
      {#each columns as col (col.key)}
        <Table.Head class={col.align === "right" ? "text-right" : undefined} style={col.width ? `width: ${col.width}` : undefined}>
          {#if col.sortable}
            <Button
              type="button"
              variant="bare"
              onclick={() => toggleSort(col)}
              aria-sort={sortKey === col.key ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
              class="inline-flex items-center gap-1 font-medium hover:text-foreground"
            >
              {col.label}
              {#if sortKey === col.key}
                <span aria-hidden="true">{sortDir === "asc" ? "↑" : "↓"}</span>
              {/if}
            </Button>
          {:else}
            {col.label}
          {/if}
        </Table.Head>
      {/each}
    </Table.Row>
  </Table.Header>
  <Table.Body>
    {#each sortedRows as row, i (getRowKey(row, i))}
      {@const rowKey = getRowKey(row, i)}
      <Table.Row
        class={cn(detail && "cursor-pointer", expanded === rowKey && "bg-muted/50")}
        onclick={() => toggleRow(rowKey)}
        aria-expanded={detail ? expanded === rowKey : undefined}
      >
        {#each columns as col (col.key)}
          <Table.Cell class={col.align === "right" ? "text-right tabular-nums" : undefined}>
            {#if col.numeric}
              <NumericValue value={Number(row[col.key] ?? 0)} currency={col.currency} />
            {:else if col.date}
              {formatDate(row[col.key])}
            {:else}
              {row[col.key] ?? ""}
            {/if}
          </Table.Cell>
        {/each}
      </Table.Row>
      {#if detail && expanded === rowKey}
        <Table.Row class="bg-muted/30 hover:bg-muted/30">
          <Table.Cell colspan={columns.length} class="p-4">
            {@render detail(row)}
          </Table.Cell>
        </Table.Row>
      {/if}
    {/each}
  </Table.Body>
</Table.Root>
</div>
