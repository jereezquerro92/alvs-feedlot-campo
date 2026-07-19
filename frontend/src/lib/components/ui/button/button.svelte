<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts" module>
  
  export const buttonVariants = {
    variant: {
      default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
      secondary:
        "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
      destructive: "bg-destructive text-white shadow-sm hover:bg-destructive/90",
      outline:
        "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
      ghost: "hover:bg-accent hover:text-accent-foreground",
      /** A navigating link should carry `href` so the base renders a real
       * `<a>`; `variant="link"` without `href` is an action styled as a
       * link, not an anchor (issue #173). */
      link: "text-primary underline-offset-4 hover:underline",
      /** Behavior-only: no chrome and no size classes — the caller owns every
       * visual decision while still inheriting cursor, focus ring, transition,
       * and disabled affordance from the base. For controls styled as
       * non-button surfaces (tiles, chips, headers, triggers). */
      bare: "",
    },
    size: {
      default: "h-9 px-4 py-2",
      sm: "h-8 rounded-md px-3 text-xs",
      lg: "h-10 rounded-md px-8",
      icon: "h-9 w-9",
    },
  } as const;

  export type ButtonVariant = keyof typeof buttonVariants.variant;
  export type ButtonSize = keyof typeof buttonVariants.size;
</script>

<script lang="ts">
  import { cn } from "$lib/utils";

  let {
    class: className = undefined,
    variant = "default",
    size = "default",
    href = undefined,
    type = "button",
    children,
    ...rest
  }: {
    class?: string;
    variant?: ButtonVariant;
    size?: ButtonSize;
    href?: string;
    type?: "button" | "submit" | "reset";
    children?: import("svelte").Snippet;
    [key: string]: unknown;
  } = $props();

  const behavior =
    "cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50";
  const chrome =
    "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium";
  const classes = $derived(
    variant === "bare"
      ? cn(behavior, className)
      : cn(
          behavior,
          chrome,
          buttonVariants.variant[variant],
          buttonVariants.size[size],
          className,
        ),
  );
</script>

{#if href}
  <a {href} class={classes} {...rest}>{@render children?.()}</a>
{:else}
  <button {type} class={classes} {...rest}>{@render children?.()}</button>
{/if}
