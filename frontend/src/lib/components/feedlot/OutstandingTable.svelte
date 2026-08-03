<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Per-charge outstanding for one client's account: each debit with how much of it a
  payment has already been imputed against, and what is still outstanding
  ([[adr-41-payment-allocation]] decision 4). Read-only — it DISPLAYS state the
  backend derives on read (`GET /api/clients/{id}/outstanding/`); it posts nothing
  and stores nothing. Imputation moves NO balance (adr-41 decision 1): the credit
  already moved it when the payment posted. Mounts with zero props (empty state) and
  never throws ([[adr-22-showcase-ready-components]] rule 1); a bare mount performs
  no request (rule 2). Copy Spanish, keys English ([[LOCALIZATION]]).
-->
<script lang="ts">
  import * as Table from "$lib/components/ui/table";
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";

  type Charge = {
    entry: number;
    date?: string;
    concept?: string;
    amount?: string | number | null;
    allocated?: string | number | null;
    outstanding?: string | number | null;
  };

  let {
    charges = [],
    copy = {
      date: "Fecha",
      concept: "Concepto",
      amount: "Cargo (ARS)",
      allocated: "Imputado (ARS)",
      outstanding: "Pendiente (ARS)",
    },
    emptyLabel = "La cuenta no tiene cargos.",
  }: {
    charges?: Charge[];
    copy?: {
      date: string;
      concept: string;
      amount: string;
      allocated: string;
      outstanding: string;
    };
    emptyLabel?: string;
  } = $props();

  // Rendered labels live only in the frontend output ([[LOCALIZATION]]); the model
  // stores the English keys — same mapping LedgerTable uses.
  const CONCEPTS: Record<string, string> = {
    feeding: "Alimentación",
    health: "Sanidad",
    service: "Servicio",
    adjustment: "Ajuste",
    payment: "Pago",
  };

  function num(v: unknown): number {
    if (v === null || v === undefined || v === "") return 0;
    const n = Number(v);
    return Number.isNaN(n) ? 0 : n;
  }
  function str(v: unknown): string {
    return v === null || v === undefined ? "" : String(v);
  }

  const rows = $derived(
    charges.map((c) => ({
      entry: c.entry,
      date: str(c.date),
      concept: CONCEPTS[str(c.concept)] ?? str(c.concept) ?? "—",
      amount: num(c.amount),
      allocated: num(c.allocated),
      outstanding: num(c.outstanding),
    })),
  );
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
        <Table.Head class="text-right">{copy.amount}</Table.Head>
        <Table.Head class="text-right">{copy.allocated}</Table.Head>
        <Table.Head class="text-right">{copy.outstanding}</Table.Head>
      </Table.Row>
    </Table.Header>
    <Table.Body>
      {#each rows as r (r.entry)}
        <Table.Row>
          <Table.Cell class="tabular-nums text-muted-foreground">{r.date || "—"}</Table.Cell>
          <Table.Cell class="font-medium">{r.concept}</Table.Cell>
          <Table.Cell class="text-right tabular-nums">{formatNumber(r.amount, "ARS")}</Table.Cell>
          <Table.Cell class="text-right tabular-nums text-success">
            {r.allocated > 0 ? formatNumber(r.allocated, "ARS") : "—"}
          </Table.Cell>
          <Table.Cell
            class="text-right font-medium tabular-nums {r.outstanding > 0 ? '' : 'text-muted-foreground'}"
          >
            {formatNumber(r.outstanding, "ARS")}
          </Table.Cell>
        </Table.Row>
      {/each}
    </Table.Body>
  </Table.Root>
{/if}
