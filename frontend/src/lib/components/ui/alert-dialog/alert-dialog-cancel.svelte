<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { Button, type ButtonSize } from "$lib/components/ui/button";
  import { getAlertDialogCtx } from "./alert-dialog.svelte";

  const ctx = getAlertDialogCtx();

  let {
    class: className = undefined,
    size = "default",
    onclick,
    children,
    ...rest
  }: {
    class?: string;
    size?: ButtonSize;
    onclick?: (e: MouseEvent) => void;
    children?: import("svelte").Snippet;
    [key: string]: unknown;
  } = $props();

  function handleClick(e: MouseEvent): void {
    onclick?.(e);
    ctx.setOpen(false);
  }
</script>

<Button type="button" variant="outline" {size} class={className} onclick={handleClick} {...rest}>
  {@render children?.()}
</Button>
