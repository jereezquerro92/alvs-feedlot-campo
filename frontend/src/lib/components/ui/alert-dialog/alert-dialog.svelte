<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts" module>
  import { getContext, setContext } from "svelte";

  const KEY = Symbol("alert-dialog");

  export interface AlertDialogCtx {
    open: () => boolean;
    setOpen: (value: boolean) => void;
  }

  export function getAlertDialogCtx(): AlertDialogCtx {
    const ctx = getContext<AlertDialogCtx>(KEY);
    if (!ctx) throw new Error("AlertDialog.* must be used inside AlertDialog.Root");
    return ctx;
  }
</script>

<script lang="ts">
  let {
    open = $bindable(false),
    children,
  }: { open?: boolean; children?: import("svelte").Snippet } = $props();

  setContext<AlertDialogCtx>(KEY, {
    open: () => open,
    setOpen: (value: boolean) => {
      open = value;
    },
  });
</script>

{@render children?.()}
