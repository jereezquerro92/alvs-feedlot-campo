<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<!--
  Compact pill badge (avatar | display name | hamburger). The hamburger
  opens a Melt UI Popover ([[MELT-UI]]) used as a dropdown menu, hand-rolled
  directly on `melt/builders` — the same precedent nav/DropdownMenu.svelte
  sets — rather than composed from the vendored overlay/Popover component:
  that component's trigger self-renders a fixed labeled Button, which
  cannot host this badge's avatar+name+hamburger cluster.

  Menu rows (theme / profile / showcase) share SessionMenuRow — icon left,
  label right. Showcase is admins-only ([[AUTH]] Django Groups).

  Content sits behind Melt's native `popover="manual"` attribute
  (getPopover(), Popover builder source), which is hidden-by-default per
  the HTML Popover API — first paint never shows it open, only a user
  click calls `showPopover()`.

  Root cause of the #189/#373 regression (this alone WAS NOT enough): the
  popover-content divs also carried Tailwind's unconditional `flex`
  utility class. `.flex { display: flex }` is an ordinary
  author-stylesheet rule — same-or-higher cascade priority than the UA's
  built-in `[popover]:not(:popover-open) { display: none }` default — so
  `flex` WON the cascade and permanently overrode the native hidden
  state, regardless of the `popover`/`inert` attributes being
  structurally correct (verified: SSR HTML always emitted
  `popover="manual" inert` faithfully). This is why the #277 structural
  fix never held across #275/#299's re-verifications: none of them
  touched the CSS defeating the very mechanism they relied on. The
  durable fix is `[&:popover-open]:flex` in place of a bare `flex` —
  `display: flex` now applies ONLY in the open state; the UA default
  governs the closed state, unopposed.
-->
<script lang="ts">
  import { onMount } from "svelte";
  import { Popover } from "melt/builders";
  import { Button } from "$lib/components/ui/button";
  import { Avatar, AvatarImage, AvatarFallback } from "$lib/components/ui/avatar";
  import QuickThemeToggle from "$lib/components/theme/QuickThemeToggle.svelte";
  import SessionMenuRow from "$lib/components/auth/SessionMenuRow.svelte";
  import { GROUP, inAnyGroup } from "$lib/auth";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { resolveDisplayName, resolveInitials } from "$lib/display-name";
  import { cn } from "$lib/utils";
  import { t } from "../../../i18n";
  import type { Me } from "$lib/types/user";

  let {
    me = null,
    pending = false,
    publicBackendUrl = "",
    loginLabel = "",
    logoutLabel = "",
    onLogout,
  }: {
    me?: Me | null;
    /** True for an authenticated, role-less (lobby-confined) session — gates
     * the profile deep-link, since /profile/ itself redirects a pending
     * session back to / ([[adr-20-authorization-lobby]]). Defaults to
     * `false`, the more common/demo-friendly default: a bare
     * `<SessionBadge me={demoMe} />` invocation shows the profile link, a
     * plain `<a href>` navigation, not a mutating action (adr-22 rule 2). */
    pending?: boolean;
    publicBackendUrl?: string;
    /** Rendered copy arrives resolved from the page's frontmatter (LOCALIZATION) */
    loginLabel?: string;
    logoutLabel?: string;
    /** Called instead of submitting the logout form when supplied — lets a
     * caller (e.g. a gallery demo) intercept the mutating action. Defaults
     * to `undefined`, which leaves the real form submit as the action, so a
     * bare `<SessionBadge me={demoMe} />` invocation with no `me` (adr-22 r1
     * default `null`) never reaches this path in the first place. */
    onLogout?: (event: SubmitEvent) => void;
  } = $props();

  const username = $derived(resolveDisplayName(me));
  const initials = $derived(resolveInitials(me));
  const isAdmin = $derived(inAnyGroup(me, [GROUP.ADMINS]));

  let csrfToken = $state("");

  onMount(() => {
    csrfToken = readCsrfTokenFromCookie();
  });

  function handleLogoutSubmit(event: SubmitEvent): void {
    if (onLogout) {
      event.preventDefault();
      onLogout(event);
    }
  }

  const popover = new Popover({
    floatingConfig: {
      computePosition: { placement: "bottom-end" },
    },
  });
</script>

{#if me}
  <div
    class="flex items-center gap-2 rounded-full border border-border bg-card py-1 pl-1 pr-2 text-card-foreground shadow-sm"
  >
    <Avatar class="size-7!">
      {#if me.picture}
        <AvatarImage src={me.picture} alt={username} />
      {:else}
        <AvatarFallback class="text-xs">{initials}</AvatarFallback>
      {/if}
    </Avatar>
    <span class="max-w-32 truncate text-sm font-medium">{username}</span>
    <button
      type="button"
      {...popover.trigger}
      aria-label={t("auth_open_menu")}
      class={cn(
        "inline-flex size-7 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground",
      )}
    >
      <span aria-hidden="true">&#9776;</span>
    </button>
  </div>

  <div
    {...popover.content}
    class="z-50 hidden min-w-56 flex-col gap-1 rounded-md border border-border bg-popover p-2 text-popover-foreground shadow-md [&:popover-open]:flex"
  >
    <span class="truncate px-2 py-1.5 text-sm text-muted-foreground">{me.email}</span>
    <QuickThemeToggle />
    {#if !pending}
      <SessionMenuRow href="/profile/" icon="user" label={t("nav_profile")} />
      {#if isAdmin}
        <SessionMenuRow href="/showcase/components/" icon="layers" label={t("nav_showcase")} />
      {/if}
    {/if}
    <form method="post" action={`${publicBackendUrl}/accounts/logout/`} onsubmit={handleLogoutSubmit} class="pt-1">
      <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
      <Button type="submit" variant="destructive" size="sm" class="w-full">{logoutLabel}</Button>
    </form>
  </div>
{:else}
  <div class="flex items-center gap-2">
    <button
      type="button"
      {...popover.trigger}
      aria-label={t("auth_open_menu")}
      class={cn(
        "inline-flex size-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground",
      )}
    >
      <span aria-hidden="true">&#9776;</span>
    </button>
    <Button href={`${publicBackendUrl}/accounts/login/`}>{loginLabel}</Button>
  </div>

  <div
    {...popover.content}
    class="z-50 hidden min-w-40 flex-col gap-1 rounded-md border border-border bg-popover p-2 text-popover-foreground shadow-md [&:popover-open]:flex"
  >
    <QuickThemeToggle />
  </div>
{/if}
