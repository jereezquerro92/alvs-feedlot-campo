<!-- LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-04-frontend-and-design-system]] · [[adr-15-chatbot-two-tier]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[CHATBOT]]
     LIVE-DOC:END -->

<!--
  The composer only collects the user's raw utterance and hands it up via
  `onsubmit` ([[CHATBOT]]). It never renders assistant text and holds no
  actuator rights — the two-tier split (adr-15) lives above it in ChatUI.
-->
<script lang="ts">
  import { onDestroy } from "svelte";
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { createTypewriterCycle, type Scheduler } from "$lib/typewriter-placeholder";

  let {
    pending = false,
    placeholder = "Type a message",
    ariaLabel,
    sendLabel,
    placeholderExamples = [],
    onsubmit,
    class: className = undefined,
  }: {
    pending?: boolean;
    /** Rendered copy arrives resolved from the page's frontmatter (LOCALIZATION) */
    placeholder?: string;
    ariaLabel: string;
    sendLabel: string;
    /** Typewriter phrases to cycle; empty disables the cycle. */
    placeholderExamples?: string[];
    onsubmit: (text: string) => void;
    class?: string;
  } = $props();

  let value = $state("");
  let animatedPlaceholder = $state("");

  const realScheduler: Scheduler = {
    set: (cb, ms) => setTimeout(cb, ms),
    clear: (handle) => clearTimeout(handle as ReturnType<typeof setTimeout>),
  };

  const cycle = createTypewriterCycle(
    placeholderExamples,
    { typeMs: 45, holdMs: 10000, deleteMs: 25 },
    realScheduler,
  );
  cycle.onUpdate((text) => {
    animatedPlaceholder = text;
  });

  $effect(() => {
    if (value.length === 0 && placeholderExamples.length > 0) {
      cycle.start();
    } else {
      cycle.stop();
    }
  });

  onDestroy(() => cycle.stop());

  function submit(): void {
    const text = value.trim();
    if (!text || pending) return;
    value = "";
    onsubmit(text);
  }

  function handleKeydown(e: KeyboardEvent): void {
    if (e.key === "Enter") {
      e.preventDefault();
      submit();
    }
  }
</script>

<div class={`flex items-center gap-2 ${className ?? ""}`}>
  <div class="relative flex-1">
    <Input
      bind:value
      onkeydown={handleKeydown}
      placeholder={value.length === 0 && placeholderExamples.length === 0 ? placeholder : ""}
      aria-label={ariaLabel}
      disabled={pending}
    />
    {#if value.length === 0 && animatedPlaceholder}
      <span
        class="pointer-events-none absolute inset-y-0 left-3 flex items-center text-sm text-muted-foreground"
      >
        {animatedPlaceholder}
      </span>
    {/if}
  </div>
  <Button type="button" onclick={submit} disabled={!value.trim() || pending}>
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      class="h-4 w-4"
      aria-hidden="true"
    >
      <path d="M22 2 11 13" />
      <path d="M22 2 15 22l-4-9-9-4Z" />
    </svg>
    {sendLabel}
  </Button>
</div>
