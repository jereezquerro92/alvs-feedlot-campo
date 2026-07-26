<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The current-account extract: the client's immutable ledger entries with a
  running balance ([[adr-25-account-ledger]] rules 1–2). Read-only — it displays
  entries derived in the backend and computes no economic truth of its own; the
  running balance is a presentation of Σ debits − Σ credits (positive = the client
  owes, adr-25 rule 2). Entries arrive newest-first; the running balance is walked
  oldest→newest and shown back newest-first. Mounts with zero props (empty state)
  and never throws ([[adr-22-showcase-ready-components]] rule 1); a bare mount
  performs no request (rule 2). Copy Spanish, keys English ([[LOCALIZATION]]).
-->
<script lang="ts">
  import * as Table from "$lib/components/ui/table";
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";

  type Entry = {
    id: number;
    date?: string;
    direction?: string;
    amount?: string | number | null;
    concept?: string;
    description?: string;
  };

  let {
    entries = [],
    copy = {
      date: "Fecha",
      concept: "Concepto",
      description: "Detalle",
      debit: "Débito (ARS)",
      credit: "Crédito (ARS)",
      balance: "Saldo (ARS)",
    },
    emptyLabel = "La cuenta no tiene movimientos.",
  }: {
    entries?: Entry[];
    copy?: {
      date: string;
      concept: string;
      description: string;
      debit: string;
      credit: string;
      balance: string;
    };
    emptyLabel?: string;
  } = $props();

  // Rendered labels live only in the frontend output ([[LOCALIZATION]]); the model
  // stores the English keys. Same in-component mapping ClientsTable uses for kinds.
  const CONCEPTS: Record<string, string> = {
    feeding: "Alimentación",
    health: "Sanidad",
    service: "Servicio",
    adjustment: "Ajuste",
    payment: "Pago",
  };

  function num(v: unknown): number | null {
    if (v === null || v === undefined || v === "") return null;
    const n = Number(v);
    return Number.isNaN(n) ? null : n;
  }
  function str(v: unknown): string {
    return v === null || v === undefined ? "" : String(v);
  }

  // Entries come newest-first (`-date, -id`). Walk oldest→newest to accumulate the
  // running balance, then hand the rows back newest-first for display.
  const rows = $derived.by(() => {
    const chrono = entries.slice().reverse();
    let running = 0;
    const out = chrono.map((e) => {
      const amount = num(e.amount) ?? 0;
      const isDebit = e.direction === "debit";
      running += isDebit ? amount : -amount;
      return {
        id: e.id,
        date: str(e.date),
        concept: CONCEPTS[str(e.concept)] ?? str(e.concept) ?? "—",
        description: str(e.description),
        debit: isDebit ? amount : null,
        credit: isDebit ? null : amount,
        balance: running,
      };
    });
    out.reverse();
    return out;
  });
</script>

{#if rows.length === 0}
  <p class="rounded-md border border-dashed border-border/50 p-6 text-center text-sm text-muted-foreground">
    {emptyLabel}
  </p>
{:else}
  <Table.Root>
    <Table.Header>
      <Table.Row>
        <Table.Head>{copy.date}</Table.Head>
        <Table.Head>{copy.concept}</Table.Head>
        <Table.Head>{copy.description}</Table.Head>
        <Table.Head class="text-right">{copy.debit}</Table.Head>
        <Table.Head class="text-right">{copy.credit}</Table.Head>
        <Table.Head class="text-right">{copy.balance}</Table.Head>
      </Table.Row>
    </Table.Header>
    <Table.Body>
      {#each rows as r (r.id)}
        <Table.Row>
          <Table.Cell class="tabular-nums text-muted-foreground">{r.date || "—"}</Table.Cell>
          <Table.Cell class="font-medium">{r.concept}</Table.Cell>
          <Table.Cell class="text-muted-foreground">{r.description || "—"}</Table.Cell>
          <Table.Cell class="text-right tabular-nums">
            {r.debit === null ? "—" : formatNumber(r.debit, "ARS")}
          </Table.Cell>
          <Table.Cell class="text-right tabular-nums text-success">
            {r.credit === null ? "—" : formatNumber(r.credit, "ARS")}
          </Table.Cell>
          <Table.Cell class="text-right font-medium tabular-nums">
            {formatNumber(r.balance, "ARS")}
          </Table.Cell>
        </Table.Row>
      {/each}
    </Table.Body>
  </Table.Root>
{/if}
