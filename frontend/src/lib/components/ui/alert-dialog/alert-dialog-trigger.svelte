<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { getAlertDialogCtx } from "./alert-dialog.svelte";

  const ctx = getAlertDialogCtx();

  let { class: className = undefined, children, ...rest }: {
    class?: string; children?: import("svelte").Snippet; [key: string]: unknown;
  } = $props();
</script>

<Button
  type="button"
  variant="bare"
  class={className}
  onclick={() => ctx.setOpen(true)}
  {...rest}
>{@render children?.()}</Button>
