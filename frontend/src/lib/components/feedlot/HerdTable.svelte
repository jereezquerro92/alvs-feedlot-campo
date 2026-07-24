<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The herd of one client: its anonymous/named lots and its individual animals
  ([[adr-26-livestock-individual-and-lot]]). Two small tables in one card.
  Mounts with zero props (both sections show their empty state) and never throws
  ([[adr-22-showcase-ready-components]] rule 1).
-->
<script lang="ts">
  import * as Table from "$lib/components/ui/table";
  import { Badge } from "$lib/components/ui/badge";
  import { formatNumber } from "$lib/components/data/NumericValue.svelte";

  type Lot = {
    id: number;
    code?: string;
    mode?: string;
    head_count?: number;
    total_weight?: string | number;
    status?: string;
  };
  type Animal = {
    id: number;
    ear_tag?: string;
    category?: string;
    current_weight?: string | number | null;
    status?: string;
  };

  let {
    lots = [],
    animals = [],
    copy = {
      lotsTitle: "Lotes",
      animalsTitle: "Animales",
      code: "Código",
      headCount: "Cabezas",
      totalWeight: "Peso total (kg)",
      status: "Estado",
      earTag: "Caravana",
      category: "Categoría",
      currentWeight: "Peso actual (kg)",
      emptyLots: "Sin lotes.",
      emptyAnimals: "Sin animales individuales.",
    },
  }: {
    lots?: Lot[];
    animals?: Animal[];
    copy?: {
      lotsTitle: string;
      animalsTitle: string;
      code: string;
      headCount: string;
      totalWeight: string;
      status: string;
      earTag: string;
      category: string;
      currentWeight: string;
      emptyLots: string;
      emptyAnimals: string;
    };
  } = $props();

  const CATEGORIES: Record<string, string> = {
    cow: "Vaca",
    bull: "Toro",
    steer: "Novillo",
    heifer: "Vaquillona",
    calf: "Ternero/a",
  };
  const STATUS: Record<string, string> = {
    active: "Activo",
    dead: "Muerto",
    sold: "Vendido",
    exited: "Egresado",
    closed: "Cerrado",
  };
  const STATUS_VARIANT: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
    active: "default",
    dead: "destructive",
    sold: "secondary",
    exited: "secondary",
    closed: "outline",
  };

  function kg(v: string | number | null | undefined): string {
    if (v === null || v === undefined || v === "") return "—";
    const n = Number(v);
    return Number.isNaN(n) ? "—" : formatNumber(n, undefined, "es", 0);
  }
</script>

<div class="flex flex-col gap-6">
  <section class="flex flex-col gap-2">
    <h3 class="text-sm font-semibold text-muted-foreground">{copy.lotsTitle}</h3>
    {#if lots.length === 0}
      <p class="text-sm text-muted-foreground">{copy.emptyLots}</p>
    {:else}
      <Table.Root>
        <Table.Header>
          <Table.Row>
            <Table.Head>{copy.code}</Table.Head>
            <Table.Head class="text-right">{copy.headCount}</Table.Head>
            <Table.Head class="text-right">{copy.totalWeight}</Table.Head>
            <Table.Head>{copy.status}</Table.Head>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {#each lots as l (l.id)}
            <Table.Row>
              <Table.Cell class="font-medium">{l.code || "—"}</Table.Cell>
              <Table.Cell class="text-right tabular-nums">{l.head_count ?? "—"}</Table.Cell>
              <Table.Cell class="text-right tabular-nums">{kg(l.total_weight)}</Table.Cell>
              <Table.Cell>
                <Badge variant={STATUS_VARIANT[l.status ?? ""] ?? "outline"}>
                  {STATUS[l.status ?? ""] ?? l.status ?? "—"}
                </Badge>
              </Table.Cell>
            </Table.Row>
          {/each}
        </Table.Body>
      </Table.Root>
    {/if}
  </section>

  <section class="flex flex-col gap-2">
    <h3 class="text-sm font-semibold text-muted-foreground">{copy.animalsTitle}</h3>
    {#if animals.length === 0}
      <p class="text-sm text-muted-foreground">{copy.emptyAnimals}</p>
    {:else}
      <Table.Root>
        <Table.Header>
          <Table.Row>
            <Table.Head>{copy.earTag}</Table.Head>
            <Table.Head>{copy.category}</Table.Head>
            <Table.Head class="text-right">{copy.currentWeight}</Table.Head>
            <Table.Head>{copy.status}</Table.Head>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {#each animals as a (a.id)}
            <Table.Row>
              <Table.Cell class="font-medium">{a.ear_tag || "—"}</Table.Cell>
              <Table.Cell>{CATEGORIES[a.category ?? ""] ?? a.category ?? "—"}</Table.Cell>
              <Table.Cell class="text-right tabular-nums">{kg(a.current_weight)}</Table.Cell>
              <Table.Cell>
                <Badge variant={STATUS_VARIANT[a.status ?? ""] ?? "outline"}>
                  {STATUS[a.status ?? ""] ?? a.status ?? "—"}
                </Badge>
              </Table.Cell>
            </Table.Row>
          {/each}
        </Table.Body>
      </Table.Root>
    {/if}
  </section>
</div>
