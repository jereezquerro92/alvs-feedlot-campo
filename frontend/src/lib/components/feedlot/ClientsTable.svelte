<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The feedlot clients list. Each row links to its dashboard. Mounts with zero
  props (renders the empty state) and never throws
  ([[adr-22-showcase-ready-components]] rule 1). Read-only: no mutating action on
  a bare mount ([[adr-22-showcase-ready-components]] rule 2).
-->
<script lang="ts">
  import * as Table from "$lib/components/ui/table";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";

  type Client = {
    id: number;
    name: string;
    kind?: string;
    tax_id?: string;
    balance?: string | number | null;
  };

  let {
    clients = [],
    columns = {
      name: "Cliente",
      kind: "Tipo",
      taxId: "CUIT",
      balance: "Saldo (ARS)",
      action: "",
    },
    detailLabel = "Ver panel",
    emptyLabel = "Todavía no hay clientes cargados.",
  }: {
    clients?: Client[];
    columns?: { name: string; kind: string; taxId: string; balance: string; action: string };
    detailLabel?: string;
    emptyLabel?: string;
  } = $props();

  const KINDS: Record<string, string> = {
    boarding: "Hotelería",
    own: "Hacienda propia",
  };

  function balanceOf(c: Client): number | null {
    if (c.balance === null || c.balance === undefined || c.balance === "") return null;
    const n = Number(c.balance);
    return Number.isNaN(n) ? null : n;
  }
</script>

{#if clients.length === 0}
  <p class="rounded-md border border-dashed border-border/50 p-6 text-center text-sm text-muted-foreground">
    {emptyLabel}
  </p>
{:else}
  <Table.Root>
    <Table.Header>
      <Table.Row>
        <Table.Head>{columns.name}</Table.Head>
        <Table.Head>{columns.kind}</Table.Head>
        <Table.Head>{columns.taxId}</Table.Head>
        <Table.Head class="text-right">{columns.balance}</Table.Head>
        <Table.Head class="text-right">{columns.action}</Table.Head>
      </Table.Row>
    </Table.Header>
    <Table.Body>
      {#each clients as c (c.id)}
        {@const balance = balanceOf(c)}
        <Table.Row>
          <Table.Cell class="font-medium">{c.name}</Table.Cell>
          <Table.Cell>
            <Badge variant="outline">{KINDS[c.kind ?? ""] ?? c.kind ?? "—"}</Badge>
          </Table.Cell>
          <Table.Cell class="text-muted-foreground">{c.tax_id || "—"}</Table.Cell>
          <Table.Cell class="text-right tabular-nums">
            {balance === null ? "—" : formatNumber(balance, "ARS")}
          </Table.Cell>
          <Table.Cell class="text-right">
            <Button href={`/feedlot/${c.id}/`} variant="secondary" size="sm">{detailLabel}</Button>
          </Table.Cell>
        </Table.Row>
      {/each}
    </Table.Body>
  </Table.Root>
{/if}
