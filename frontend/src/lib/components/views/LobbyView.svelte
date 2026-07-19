<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     LIVE-DOC:END -->

<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { SectionTitle } from "$lib/components/primitives/titles";
  import * as Card from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { Separator } from "$lib/components/ui/separator";
  import { Alert, AlertTitle, AlertDescription } from "$lib/components/ui/alert";

  type LobbyCopy = {
    title: string;
    intro: string;
    deniedTitle: string;
    deniedBody: string;
    pendingTitle: string;
    pendingBody: string;
    navTitle: string;
    navShowcase: string;
    navChatui: string;
    m365Title: string;
  };

  let {
    projectSlug = "",
    denied = false,
    pending = false,
    authenticated = false,
    copy = {} as LobbyCopy,
    hello = "",
    world = "",
  }: {
    projectSlug?: string;
    denied?: boolean;
    pending?: boolean;
    authenticated?: boolean;
    copy?: LobbyCopy;
    hello?: string;
    world?: string;
  } = $props();
</script>

<div class="min-h-screen flex flex-col">
  <header class="flex w-full items-center justify-between gap-4 px-6 pt-8 sm:px-10">
    <Badge variant="outline" class="text-sm font-semibold tracking-wide">{projectSlug}</Badge>
    <slot name="session" />
  </header>

  <main class="flex flex-1 flex-col items-center justify-center gap-8 px-6 py-12">
    <div class="flex flex-col items-center gap-2 text-center">
      <SectionTitle as="h1">{copy.title}</SectionTitle>
      <p class="max-w-md text-muted-foreground">{copy.intro}</p>
    </div>

    {#if denied}
      <Alert variant="destructive" class="w-full max-w-sm">
        <AlertTitle>{copy.deniedTitle}</AlertTitle>
        <AlertDescription>{copy.deniedBody}</AlertDescription>
      </Alert>
    {/if}

    {#if pending}
      <Card.Root class="w-full max-w-sm border-border/40 shadow-sm">
        <Card.Header>
          <Card.Title>{copy.pendingTitle}</Card.Title>
        </Card.Header>
        <Card.Content>
          <p class="text-sm text-muted-foreground">{copy.pendingBody}</p>
        </Card.Content>
      </Card.Root>
    {:else}
      <Card.Root class="w-full max-w-sm border-border/40 shadow-sm">
        <Card.Header>
          <Card.Title>{copy.navTitle}</Card.Title>
        </Card.Header>
        <Card.Content class="flex flex-col gap-3">
          <Button href="/showcase/components/" class="w-full">{copy.navShowcase}</Button>
          <Button href="/chatui/" variant="secondary" class="w-full">{copy.navChatui}</Button>
        </Card.Content>
      </Card.Root>

      {#if authenticated}
        <Separator class="w-full max-w-sm" />

        <Card.Root class="w-full max-w-sm border-border/40 shadow-sm">
          <Card.Header>
            <Card.Title>{copy.m365Title}</Card.Title>
          </Card.Header>
          <Card.Content class="flex flex-col gap-2 pt-0">
            <span class="text-sm">{hello}</span>
            <span class="text-sm">{world}</span>
          </Card.Content>
        </Card.Root>
      {/if}
    {/if}
  </main>
</div>
