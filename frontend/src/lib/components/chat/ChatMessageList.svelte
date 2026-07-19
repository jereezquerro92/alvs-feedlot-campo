<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-15-chatbot-two-tier]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[CHATBOT]]
     LIVE-DOC:END -->

<!--
  Renders ONLY the closed set of router outcomes ([[CHATBOT]], adr-15): the
  user's own utterance, a `navigate` link, a `confirm` action, or a fixed
  status line. There is no assistant-prose branch — the router emits an enum
  member, never free text, so this list has nowhere to render generated text.
-->
<script lang="ts" module>
  export type ChatMessage =
    | { id: string; role: "user"; text: string }
    | { id: string; role: "navigate"; label: string; target: string }
    | { id: string; role: "confirm"; label: string; target: string }
    | { id: string; role: "status"; text: string };
</script>

<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { Alert, AlertDescription } from "$lib/components/ui/alert";
  import * as Card from "$lib/components/ui/card";
  import ConfirmDialog from "$lib/components/overlay/ConfirmDialog.svelte";

  let {
    messages,
    onconfirm = undefined,
    copy,
  }: {
    messages: ChatMessage[];
    /** Fired when the user confirms a `confirm` outcome in its dialog. */
    onconfirm?: (message: Extract<ChatMessage, { role: "confirm" }>) => void;
    /** Rendered copy arrives resolved from the page's frontmatter (LOCALIZATION) */
    copy: { go: string; confirm: string };
  } = $props();
</script>

<!--
  Array/DOM order stays natural append order (oldest -> newest, unchanged
  from ChatUI's push()) — no reversal here. Bottom anchoring is owned by
  ChatUI's wrapping container (justify-end + a scrollTop-to-bottom effect),
  not by this component, so reading/tab/DOM order is correct by
  construction (issue #250).
-->
<div class="flex flex-col gap-3">
  {#each messages as message (message.id)}
    {#if message.role === "user"}
      <div class="flex justify-end">
        <div class="max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-4 py-2 text-sm text-primary-foreground">
          {message.text}
        </div>
      </div>
    {:else if message.role === "navigate"}
      <Card.Root class="max-w-[85%] self-start">
        <Card.Content class="flex items-center justify-between gap-4 py-3">
          <span class="text-sm">{message.label}</span>
          <Button href={message.target} size="sm">{copy.go}</Button>
        </Card.Content>
      </Card.Root>
    {:else if message.role === "confirm"}
      <Card.Root class="max-w-[85%] self-start">
        <Card.Content class="flex items-center justify-between gap-4 py-3">
          <span class="text-sm">{message.label}</span>
          <ConfirmDialog
            title={message.label}
            confirmLabel={copy.confirm}
            triggerLabel={copy.confirm}
            onconfirm={() => onconfirm?.(message)}
          />
        </Card.Content>
      </Card.Root>
    {:else}
      <Alert class="max-w-[85%] self-start">
        <AlertDescription>{message.text}</AlertDescription>
      </Alert>
    {/if}
  {/each}
</div>
