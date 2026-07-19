<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import * as AlertDialog from "$lib/components/ui/alert-dialog";
  import { Button } from "$lib/components/ui/button";

  let {
    open = $bindable(false),
    title,
    description = undefined,
    confirmLabel = "Confirm",
    cancelLabel = "Cancel",
    triggerLabel = undefined,
    triggerIcon = undefined,
    onconfirm,
  }: {
    open?: boolean;
    title: string;
    description?: string;
    confirmLabel?: string;
    cancelLabel?: string;
    /** Text label for the trigger; omit for an icon-only trigger. */
    triggerLabel?: string;
    /** Snippet rendered inside the trigger, for an icon-only affordance. */
    triggerIcon?: import("svelte").Snippet;
    onconfirm: () => void;
  } = $props();
</script>

<AlertDialog.Root bind:open>
  <AlertDialog.Trigger>
    {#if triggerIcon}
      {@render triggerIcon()}
    {:else}
      <Button type="button" aria-label={triggerLabel ?? confirmLabel}>
        {triggerLabel ?? confirmLabel}
      </Button>
    {/if}
  </AlertDialog.Trigger>
  <AlertDialog.Content>
    <AlertDialog.Header>
      <AlertDialog.Title>{title}</AlertDialog.Title>
      {#if description}
        <AlertDialog.Description>{description}</AlertDialog.Description>
      {/if}
    </AlertDialog.Header>
    <AlertDialog.Footer>
      <AlertDialog.Cancel>{cancelLabel}</AlertDialog.Cancel>
      <AlertDialog.Action onclick={onconfirm}>{confirmLabel}</AlertDialog.Action>
    </AlertDialog.Footer>
  </AlertDialog.Content>
</AlertDialog.Root>
