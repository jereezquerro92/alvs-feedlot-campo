<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Toast notifications on the melt/builders Toaster ([[MELT-UI]]) — the
  builder owns the native Popover-API region, auto-dismiss timers, and
  hover/tab-visibility pausing. `toaster` is a module-level singleton: import
  it anywhere to push a toast; mount this component once (e.g. the root
  layout) to render the region.
-->
<script lang="ts" module>
  import { Toaster } from "melt/builders";

  export type ToastVariant = "default" | "success" | "error";

  export type ToastData = {
    title: string;
    description?: string;
    variant?: ToastVariant;
  };

  /** Shared toaster — call `toaster.addToast({ data: {...} })` from anywhere. */
  export const toaster = new Toaster<ToastData>();
</script>

<script lang="ts">
  import { cn } from "$lib/utils";

  let { class: className = undefined }: { class?: string } = $props();

  const variantBorder: Record<ToastVariant, string> = {
    default: "border-border",
    success: "border-primary",
    error: "border-destructive",
  };
</script>

<div
  {...toaster.root}
  class={cn(
    "fixed inset-auto bottom-4 right-4 z-50 m-0 flex w-80 flex-col gap-2 border-0 bg-transparent p-0",
    className,
  )}
>
  {#each toaster.toasts as toast (toast.id)}
    <div
      {...toast.content}
      class={cn(
        "flex items-start gap-3 rounded-lg border bg-popover p-4 text-sm text-popover-foreground shadow-lg",
        variantBorder[toast.data.variant ?? "default"],
      )}
    >
      <div class="flex-1">
        <p {...toast.title} class="font-medium">{toast.data.title}</p>
        {#if toast.data.description}
          <p {...toast.description} class="text-muted-foreground">{toast.data.description}</p>
        {/if}
      </div>
      <button
        {...toast.close}
        class="cursor-pointer text-muted-foreground hover:text-foreground"
        aria-label="Dismiss"
      >✕</button>
    </div>
  {/each}
</div>
