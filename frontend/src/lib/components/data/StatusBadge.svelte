<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts" module>
  import type { BadgeVariant } from "$lib/components/ui/badge/badge.svelte";

  export type StatusEntry = { label: string; variant: BadgeVariant };

  /**
   * Default status → badge variant mapping; override per project via the `map` prop.
   * No baked labels here — the raw status key is the label unless a caller-supplied
   * `map` entry provides one (see issue #265 item 4, [[LOCALIZATION]]).
   */
  export const DEFAULT_STATUS_MAP: Record<string, StatusEntry> = {
    approved: { label: "approved", variant: "success" },
    ok: { label: "ok", variant: "success" },
    paid: { label: "paid", variant: "success" },
    pending: { label: "pending", variant: "warning" },
    review: { label: "review", variant: "warning" },
    rejected: { label: "rejected", variant: "negative" },
    error: { label: "error", variant: "negative" },
    overdue: { label: "overdue", variant: "negative" },
    draft: { label: "draft", variant: "secondary" },
  };
</script>

<script lang="ts">
  import { Badge } from "$lib/components/ui/badge";

  let {
    status,
    map = DEFAULT_STATUS_MAP,
    class: className = undefined,
  }: {
    status: string;
    map?: Record<string, StatusEntry>;
    class?: string;
  } = $props();

  const entry = $derived(map[status] ?? { label: status, variant: "outline" as BadgeVariant });
</script>

<Badge variant={entry.variant} class={className}>{entry.label}</Badge>
