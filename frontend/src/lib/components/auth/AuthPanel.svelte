<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { onMount } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { resolveDisplayName } from "$lib/display-name";
  import type { Me } from "$lib/types/user";

  type AuthPanelCopy = {
    title: string;
    loggedInAs: string;
    noGroups: string;
    notSignedIn: string;
    login: string;
    logout: string;
  };

  let {
    me = null,
    publicBackendUrl = "",
    copy = {} as AuthPanelCopy,
  }: {
    me?: Me | null;
    publicBackendUrl?: string;
    /** Rendered copy arrives resolved from the page's frontmatter (LOCALIZATION) */
    copy?: AuthPanelCopy;
  } = $props();

  const username = $derived(resolveDisplayName(me));

  let csrfToken = $state("");

  onMount(() => {
    csrfToken = readCsrfTokenFromCookie();
  });
</script>

<section class="flex flex-col gap-3">
  <h2 class="text-xl font-semibold">{copy.title}</h2>
  <Card.Root>
    <Card.Content class="pt-6">
      {#if me}
        <div class="flex flex-col gap-3">
          <p>{copy.loggedInAs} <strong>{username || me.sub}</strong></p>
          <div class="flex flex-wrap gap-2">
            {#if me.groups.length > 0}
              {#each me.groups as g (g)}
                <Badge variant="secondary">{g}</Badge>
              {/each}
            {:else}
              <span class="text-sm text-muted-foreground">{copy.noGroups}</span>
            {/if}
          </div>
          <form method="post" action={`${publicBackendUrl}/accounts/logout/`}>
            <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
            <Button type="submit" variant="destructive">{copy.logout}</Button>
          </form>
        </div>
      {:else}
        <div class="flex flex-col gap-3">
          <p class="text-muted-foreground">{copy.notSignedIn}</p>
          <Button href={`${publicBackendUrl}/accounts/login/`}>{copy.login}</Button>
        </div>
      {/if}
    </Card.Content>
  </Card.Root>
</section>
