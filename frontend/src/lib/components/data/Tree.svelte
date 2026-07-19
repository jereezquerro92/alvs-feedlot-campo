<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Hierarchical expandable tree on the melt/builders Tree ([[MELT-UI]]) — the
  builder owns selection, expansion, keyboard navigation (arrows, typeahead),
  and the group/item ARIA roles; this component is the styled shell and its
  own recursion. `<svelte:self>` renders one node per call: the outer call (no
  `node` prop) builds the `Tree` instance from `items` and walks its top-level
  `children`; each recursive call renders one `Child` and, if it has
  sub-items, recurses again into its `children`. `items` defaults to a sample
  holding/intercompany hierarchy so a zero-prop invocation still renders
  without throwing (adr-22 r1) and fires no mutating call (adr-22 r2).
-->
<script lang="ts" module>
  export type TreeNodeData = {
    id: string;
    label: string;
    children?: TreeNodeData[];
  };
</script>

<script lang="ts">
  import { Tree } from "melt/builders";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";

  const sampleItems: TreeNodeData[] = [
    {
      id: "holding",
      label: t("demo_tree_holding"),
      children: [
        {
          id: "acme",
          label: "Acme Corp",
          children: [
            { id: "acme-payable", label: t("demo_tree_payable") },
            { id: "acme-receivable", label: t("demo_tree_receivable") },
          ],
        },
        {
          id: "nimbus",
          label: "Nimbus Ltd",
          children: [{ id: "nimbus-payable", label: t("demo_tree_payable") }],
        },
      ],
    },
  ];

  let {
    items = sampleItems,
    node = undefined,
    treeInstance = undefined,
    class: className = undefined,
  }: {
    items?: TreeNodeData[];
    /** Internal — the node this recursive call renders; unset means root. */
    node?: ReturnType<Tree<TreeNodeData>["children"]>[number];
    /** Internal — the shared builder instance, threaded through recursion. */
    treeInstance?: Tree<TreeNodeData>;
    class?: string;
  } = $props();

  const tree = node ? treeInstance! : new Tree<TreeNodeData>({ items: () => items });
</script>

{#if !node}
  <ul {...tree.root} class={cn("flex flex-col gap-0.5 text-sm", className)}>
    {#each tree.children as child (child.id)}
      <li>
        <svelte:self node={child} treeInstance={tree} />
      </li>
    {/each}
  </ul>
{:else}
  <div
    {...node.attrs}
    class={cn(
      "cursor-pointer rounded-sm px-2 py-1 outline-none",
      "hover:bg-muted focus:bg-muted",
      node.selected && "bg-primary text-primary-foreground hover:bg-primary",
    )}
  >
    {#if node.canExpand}
      <span aria-hidden="true" class={cn("mr-1 inline-block transition-transform duration-200", node.expanded && "rotate-90")}>›</span>
    {/if}
    {node.item.label}
  </div>
  {#if node.canExpand && node.expanded}
    <ul {...tree.group} class="ml-4 flex flex-col gap-0.5">
      {#each node.children ?? [] as child (child.id)}
        <li>
          <svelte:self node={child} treeInstance={tree} />
        </li>
      {/each}
    </ul>
  {/if}
{/if}
