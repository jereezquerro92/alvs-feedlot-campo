<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  The derived sanitary calendar: for one client, every scheduled dose from every
  plan enrollment, with its due date and a status — applied / pending / upcoming
  ([[adr-40-sanitary-plan-schedule]] decision 3). Read-only: it DISPLAYS what the
  backend derives (`GET /api/plan-enrollments/schedule/`) and computes no status of
  its own; the status is never stored ([[adr-24-feedlot-domain]] rule 3). Mounts with
  zero props (empty state) and never throws ([[adr-22-showcase-ready-components]]
  rule 1); a bare mount performs no request (rule 2). Copy Spanish, keys English
  ([[LOCALIZATION]]).
-->
<script lang="ts">
  import * as Table from "$lib/components/ui/table";
  import { Badge } from "$lib/components/ui/badge";

  type Item = {
    enrollment?: number;
    plan_name?: string;
    target_label?: string;
    product_name?: string;
    day_offset?: number;
    due_date?: string;
    dose?: string | number | null;
    status?: string;
  };

  let {
    items = [],
    copy = {
      plan: "Plan",
      target: "Destino",
      product: "Producto",
      due: "Vence",
      dose: "Dosis",
      status: "Estado",
    },
    statusLabels = {
      applied: "Aplicada",
      pending: "Pendiente",
      upcoming: "Próxima",
    },
    emptyLabel = "No hay planes sanitarios asignados.",
  }: {
    items?: Item[];
    copy?: {
      plan: string;
      target: string;
      product: string;
      due: string;
      dose: string;
      status: string;
    };
    statusLabels?: Record<string, string>;
    emptyLabel?: string;
  } = $props();

  function str(v: unknown): string {
    return v === null || v === undefined ? "" : String(v);
  }

  // A due-but-unapplied dose is the one that needs action → destructive; an applied
  // dose is settled → success; a future dose is informational → outline.
  const VARIANTS: Record<string, "destructive" | "secondary" | "outline"> = {
    pending: "destructive",
    applied: "secondary",
    upcoming: "outline",
  };
</script>

{#if items.length === 0}
  <p class="rounded-md border border-dashed border-border/50 p-6 text-center text-sm text-muted-foreground">
    {emptyLabel}
  </p>
{:else}
  <Table.Root>
    <Table.Header>
      <Table.Row>
        <Table.Head>{copy.plan}</Table.Head>
        <Table.Head>{copy.target}</Table.Head>
        <Table.Head>{copy.product}</Table.Head>
        <Table.Head class="tabular-nums">{copy.due}</Table.Head>
        <Table.Head class="text-right">{copy.dose}</Table.Head>
        <Table.Head>{copy.status}</Table.Head>
      </Table.Row>
    </Table.Header>
    <Table.Body>
      {#each items as it, i (`${it.enrollment}-${it.product_name}-${it.day_offset}-${i}`)}
        <Table.Row>
          <Table.Cell class="text-muted-foreground">{str(it.plan_name) || "—"}</Table.Cell>
          <Table.Cell class="font-medium">{str(it.target_label) || "—"}</Table.Cell>
          <Table.Cell>{str(it.product_name) || "—"}</Table.Cell>
          <Table.Cell class="tabular-nums text-muted-foreground">{str(it.due_date) || "—"}</Table.Cell>
          <Table.Cell class="text-right tabular-nums">{str(it.dose) || "—"}</Table.Cell>
          <Table.Cell>
            <Badge variant={VARIANTS[str(it.status)] ?? "outline"}>
              {statusLabels[str(it.status)] ?? str(it.status) ?? "—"}
            </Badge>
          </Table.Cell>
        </Table.Row>
      {/each}
    </Table.Body>
  </Table.Root>
{/if}
