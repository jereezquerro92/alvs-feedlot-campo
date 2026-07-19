<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts" module>
  export const alertVariants = {
    default: "bg-background text-foreground",
    destructive: "border-destructive/50 text-destructive [&>svg]:text-destructive",
  } as const;
  export type AlertVariant = keyof typeof alertVariants;
</script>

<script lang="ts">
  import { cn } from "$lib/utils";
  let { class: className = undefined, variant = "default", children, ...rest }: {
    class?: string; variant?: AlertVariant; children?: import("svelte").Snippet; [key: string]: unknown;
  } = $props();
</script>

<div
  role="alert"
  class={cn("relative w-full rounded-lg border px-4 py-3 text-sm", alertVariants[variant], className)}
  {...rest}
>{@render children?.()}</div>
