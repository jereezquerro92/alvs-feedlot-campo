<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { Label } from "$lib/components/ui/label";
  import { Avatar, AvatarImage, AvatarFallback } from "$lib/components/ui/avatar";
  import ConfirmDialog from "$lib/components/overlay/ConfirmDialog.svelte";
  import { Check } from "$lib/components/icons";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { resolveDisplayName, resolveInitials } from "$lib/display-name";
  import { optimisticToggle } from "$lib/optimistic-toggle";
  import type { Me } from "$lib/types/user";

  let {
    me = null,
    publicBackendUrl = "",
  }: {
    /** `null` is the zero-prop default (adr-22 rule 1): the form renders its
     * own empty state — blank nickname, fallback initials — and never throws. */
    me?: Me | null;
    publicBackendUrl?: string;
  } = $props();

  let nickname = $state(me?.nickname ?? "");
  let avatarVisible = $state(me?.avatar_visible ?? false);
  let saving = $state(false);
  let error = $state("");

  /** Reads the live-edited `nickname` rather than `me.nickname`, so the avatar
   * previews the name being typed before it is saved. */
  const initials = $derived(resolveInitials({ ...me, nickname }));
  const picture = $derived(me?.picture);

  async function patchMe(body: Record<string, unknown>): Promise<boolean> {
    saving = true;
    error = "";
    try {
      const res = await fetch(`${publicBackendUrl}/api/me/`, {
        method: "PATCH",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": readCsrfTokenFromCookie(),
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        error = `Update failed (${res.status})`;
        return false;
      }
      return true;
    } catch {
      error = "Update failed";
      return false;
    } finally {
      saving = false;
    }
  }

  function confirmNickname(): void {
    void patchMe({ nickname: nickname.trim() });
  }

  function toggleAvatarVisible(): void {
    void optimisticToggle(
      avatarVisible,
      (next) => {
        avatarVisible = next;
      },
      (next) => patchMe({ avatar_visible: next }),
    );
  }
</script>

<div class="flex w-full max-w-md flex-col gap-6">
  <div class="flex flex-col items-center gap-2">
    <Avatar class="size-16">
      {#if avatarVisible && picture}
        <AvatarImage src={picture} alt={resolveDisplayName({ ...me, nickname })} />
      {:else}
        <AvatarFallback>{initials}</AvatarFallback>
      {/if}
    </Avatar>
    <Button type="button" variant="outline" size="sm" onclick={toggleAvatarVisible} disabled={saving}>
      {avatarVisible ? "Hide avatar" : "Show avatar"}
    </Button>
  </div>

  <div class="flex flex-col gap-2">
    <Label for="nickname">Nickname</Label>
    <div class="flex items-center gap-2">
      <Input id="nickname" bind:value={nickname} placeholder="Nickname" disabled={saving} />
      {#snippet saveNicknameTrigger()}
        <Button type="button" size="icon" aria-label="Save nickname" disabled={saving}>
          <Check />
        </Button>
      {/snippet}
      <ConfirmDialog
        title="Update nickname?"
        description={`Set your nickname to "${nickname.trim()}".`}
        confirmLabel="Save"
        cancelLabel="Cancel"
        triggerIcon={saveNicknameTrigger}
        onconfirm={confirmNickname}
      />
    </div>
    {#if error}
      <p class="text-sm text-destructive">{error}</p>
    {/if}
  </div>
</div>
