<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Generic (non-alert) modal on the melt/builders Dialog — a headless builder
  that drives a native `<dialog>` via `showModal()` ([[MELT-UI]]). Melt-first
  per the layering doctrine ([[DESIGN-SYSTEM]]); the hand-rolled ui/alert-dialog
  stays for its destructive-confirm role, this covers everything else.
-->
<script lang="ts" module>
  export type { Dialog as DialogBuilder } from "melt/builders";
</script>

<script lang="ts">
  import { Dialog } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import type { ButtonVariant } from "$lib/components/ui/button/button.svelte";
  import { cn } from "$lib/utils";
  import type { Snippet } from "svelte";

  let {
    open = $bindable(false),
    title = undefined,
    description = undefined,
    triggerLabel = undefined,
    triggerVariant = "default",
    trigger = undefined,
    children,
    footer = undefined,
    closeOnOutsideClick = true,
    closeOnEscape = true,
    class: className = undefined,
  }: {
    open?: boolean;
    title?: string;
    description?: string;
    /** Renders a default Button trigger; omit to drive purely via `bind:open`. */
    triggerLabel?: string;
    triggerVariant?: ButtonVariant;
    /** Custom trigger; receives the builder so you can spread `{...d.trigger}`. */
    trigger?: Snippet<[Dialog]>;
    children: Snippet;
    footer?: Snippet;
    closeOnOutsideClick?: boolean;
    closeOnEscape?: boolean;
    class?: string;
  } = $props();

  const dialog = new Dialog({
    open: () => open,
    onOpenChange: (v) => (open = v),
    closeOnOutsideClick: () => closeOnOutsideClick,
    closeOnEscape: () => closeOnEscape,
  });
</script>

{#if trigger}
  {@render trigger?.(dialog)}
{:else if triggerLabel}
  <Button {...dialog.trigger} variant={triggerVariant}>{triggerLabel}</Button>
{/if}

<dialog
  {...dialog.content}
  aria-label={title}
  class={cn(
    "m-auto w-[calc(100%-2rem)] max-w-lg rounded-xl border bg-card p-0 text-card-foreground shadow-lg backdrop:bg-black/50",
    className,
  )}
>
  <div class="flex flex-col gap-4 p-6">
    {#if title || description}
      <div class="flex items-start justify-between gap-4">
        <div class="flex flex-col gap-1">
          {#if title}<h2 class="text-lg font-semibold leading-none tracking-tight">{title}</h2>{/if}
          {#if description}<p class="text-sm text-muted-foreground">{description}</p>{/if}
        </div>
        <Button
          variant="ghost"
          size="icon"
          class="-mr-2 -mt-2 h-8 w-8 shrink-0"
          aria-label="Close"
          onclick={() => (dialog.open = false)}
        >
          <span aria-hidden="true">✕</span>
        </Button>
      </div>
    {/if}
    {@render children?.()}
    {#if footer}
      <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        {@render footer?.()}
      </div>
    {/if}
  </div>
</dialog>
