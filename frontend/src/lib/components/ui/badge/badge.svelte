<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts" module>
  export const badgeVariants = {
    default: "border-transparent bg-primary text-primary-foreground shadow",
    secondary: "border-transparent bg-secondary text-secondary-foreground",
    destructive: "border-transparent bg-destructive text-white shadow",
    outline: "text-foreground",
    success: "border-transparent bg-success text-success-foreground shadow",
    warning: "border-transparent bg-warning text-warning-foreground shadow",
    negative: "border-transparent bg-negative text-negative-foreground shadow",
  } as const;
  export type BadgeVariant = keyof typeof badgeVariants;
</script>

<script lang="ts">
  import { cn } from "$lib/utils";
  let { class: className = undefined, variant = "default", children, ...rest }: {
    class?: string; variant?: BadgeVariant; children?: import("svelte").Snippet; [key: string]: unknown;
  } = $props();
</script>

<span
  class={cn(
    "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring",
    badgeVariants[variant],
    className,
  )}
  {...rest}
>{@render children?.()}</span>
