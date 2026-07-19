<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-15-chatbot-two-tier]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[CHATBOT]]
     LIVE-DOC:END -->

<!--
  The full router surface ([[CHATBOT]], adr-15). This is a ROUTER, not a
  chatbot: the composer sends the raw utterance to POST /api/router/route/
  ([[API]]) and the message list renders only the closed enum that comes back
  (navigate / confirm / NO_MATCH / Escalate / disabled). No free assistant
  prose is ever generated or rendered here — the generating tier is out of
  this template's scope (adr-15 rule 9).
-->
<script lang="ts">
  import ChatMessageList, { type ChatMessage } from "./ChatMessageList.svelte";
  import ChatComposer from "./ChatComposer.svelte";
  import SectionTitle from "$lib/components/primitives/titles/SectionTitle.svelte";
  import { routeUtterance, copyForResult } from "$lib/router-client";
  import { readCsrfTokenFromCookie } from "$lib/csrf";

  type ChatUICopy = {
    title: string;
    emptyState: string;
    composerPlaceholder: string;
    composerAriaLabel: string;
    composerSend: string;
    /** Typewriter phrases cycled while the composer is empty. */
    composerPlaceholderExamples?: string[];
    messageGo: string;
    messageConfirm: string;
    /** Maps a `copyForResult` message key to its resolved, localized text. */
    outcomeCopy: Record<string, string>;
  };

  const EMPTY_COPY: ChatUICopy = {
    title: "",
    emptyState: "",
    composerPlaceholder: "",
    composerAriaLabel: "",
    composerSend: "",
    messageGo: "",
    messageConfirm: "",
    outcomeCopy: {},
  };

  let {
    class: className = undefined,
    publicBackendUrl = "",
    copy = EMPTY_COPY,
  }: {
    class?: string;
    publicBackendUrl?: string;
    /** Rendered copy arrives resolved from the page's frontmatter (LOCALIZATION).
     * Defaults to blank strings (adr-22 rule 1) — a zero-prop mount renders the
     * chrome with no copy rather than throwing. */
    copy?: ChatUICopy;
  } = $props();

  let messages = $state<ChatMessage[]>([]);
  let pending = $state(false);
  let seq = 0;
  let messageContainer: HTMLDivElement | undefined = $state(undefined);

  function push(message: Omit<ChatMessage, "id">): void {
    messages = [...messages, { ...message, id: String(seq++) } as ChatMessage];
  }

  // Bottom-anchoring, imperative half: array/DOM order stays natural append
  // order (ChatMessageList renders `messages` unreversed) — `justify-end`
  // below handles the under-full case, this effect handles the overflow
  // case by pinning the scroll position to the newest message on every
  // change, with no reversal anywhere in the render path.
  $effect(() => {
    messages.length;
    if (messageContainer) messageContainer.scrollTop = messageContainer.scrollHeight;
  });

  async function handleSubmit(text: string): Promise<void> {
    push({ role: "user", text });
    pending = true;
    const result = await routeUtterance(publicBackendUrl, text, readCsrfTokenFromCookie());
    pending = false;

    if (result.kind === "outcome" && result.data.outcome === "Action") {
      const action = result.data.action;
      if (action.kind === "navigate") {
        push({ role: "navigate", label: action.label, target: action.target });
      } else {
        push({ role: "confirm", label: action.label, target: action.target });
      }
      return;
    }

    // Every non-Action result maps to fixed, frontend-owned copy keyed on the
    // outcome enum — never model-generated prose (adr-15 rule 5). The key
    // is resolved against `copy.outcomeCopy`, itself built from `t(...)`.
    const outcomeKey = copyForResult(result);
    push({ role: "status", text: (outcomeKey && copy.outcomeCopy[outcomeKey]) ?? "" });
  }

  function confirmNavigate(message: Extract<ChatMessage, { role: "confirm" }>): void {
    window.location.assign(message.target);
  }
</script>

<div class={`mx-auto flex min-h-screen w-full max-w-2xl flex-col gap-4 px-4 py-8 ${className ?? ""}`}>
  <SectionTitle as="h1">{copy.title}</SectionTitle>
  <div bind:this={messageContainer} class="flex flex-1 flex-col justify-end overflow-y-auto">
    {#if messages.length === 0}
      <p class="text-sm text-muted-foreground">
        {copy.emptyState}
      </p>
    {:else}
      <ChatMessageList
        {messages}
        onconfirm={confirmNavigate}
        copy={{ go: copy.messageGo, confirm: copy.messageConfirm }}
      />
    {/if}
  </div>
  <div class="sticky bottom-4">
    <ChatComposer
      {pending}
      onsubmit={handleSubmit}
      placeholder={copy.composerPlaceholder}
      ariaLabel={copy.composerAriaLabel}
      sendLabel={copy.composerSend}
      placeholderExamples={copy.composerPlaceholderExamples ?? []}
    />
  </div>
</div>
