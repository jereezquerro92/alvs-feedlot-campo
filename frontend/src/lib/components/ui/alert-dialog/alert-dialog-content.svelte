<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { cn } from "$lib/utils";
  import { getAlertDialogCtx } from "./alert-dialog.svelte";

  const ctx = getAlertDialogCtx();

  let { class: className = undefined, children, ...rest }: {
    class?: string; children?: import("svelte").Snippet; [key: string]: unknown;
  } = $props();

  function onKeydown(e: KeyboardEvent): void {
    if (e.key === "Escape") ctx.setOpen(false);
  }

  function onBackdropClick(): void {
    ctx.setOpen(false);
  }
</script>

{#if ctx.open()}
  <div class="fixed inset-0 z-50 flex items-center justify-center">
    <div
      class="fixed inset-0 bg-background/80"
      role="presentation"
      onclick={onBackdropClick}
    ></div>
    <div
      role="alertdialog"
      aria-modal="true"
      tabindex="-1"
      class={cn(
        "relative z-50 grid w-full max-w-lg gap-4 rounded-lg border bg-background p-6 shadow-lg",
        className,
      )}
      onkeydown={onKeydown}
      {...rest}
    >{@render children?.()}</div>
  </div>
{/if}
