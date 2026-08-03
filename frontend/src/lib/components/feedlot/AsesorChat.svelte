<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-22-showcase-ready-components]] · [[adr-53-api-membrane]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]]
     API: [[API]]
     LIVE-DOC:END -->

<!--
  The AI-advisor chat island ([[adr-35-conversational-assistant]]): a per-client Q&A
  surface over the `assistant` app. It offers MANY preset questions (grouped by the
  three advisor themes) plus a free-text box; each ask opens/uses one `Conversation`
  for the current client and POSTs a turn to `/api/conversations/{id}/messages/`,
  rendering the assistant's grounded answer. The assistant is READ-ONLY forever
  (adr-35 decision 1, adr-15 rule 1): it never acts, never posts to the ledger. The
  per-client scope is a hard backend boundary — the snapshot is built from the
  conversation's own client (adr-35 decision 2), so this island cannot reach another
  client's data even if asked. Mounts with zero props and never throws
  ([[adr-22-showcase-ready-components]] rule 1); a bare mount issues NO request until
  the user asks (rule 2). Session + CSRF per [[AUTH]]; copy via i18n ([[LOCALIZATION]]).
-->
<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Button } from "$lib/components/ui/button";
  import { readCsrfTokenFromCookie } from "$lib/csrf";
  import { t } from "../../../i18n";
  import type { MessageKey } from "../../../i18n";

  let {
    clientId = null,
    clientName = "",
    publicBackendUrl = "",
  }: {
    clientId?: number | null;
    clientName?: string;
    publicBackendUrl?: string;
  } = $props();

  type Turn = { role: "user" | "assistant"; text: string };

  // The thread built up client-side. Each POST returns the assistant answer, so we
  // never reload the page (unlike the form modules) — this is a live conversation.
  let turns = $state<Turn[]>([]);
  let conversationId = $state<number | null>(null);
  let input = $state("");
  let sending = $state(false);
  let error = $state("");

  // Preset questions, grouped by the three advisor themes (adr-27). The chip label
  // IS the question sent to the assistant. Keys resolve to Spanish rendered output.
  const groups: Array<{ title: string; keys: MessageKey[] }> = [
    {
      title: t("feedlot_asesor_group_livestock"),
      keys: [
        "feedlot_asesor_q_head",
        "feedlot_asesor_q_adg",
        "feedlot_asesor_q_conversion",
        "feedlot_asesor_q_mortality",
        "feedlot_asesor_q_lot_weights",
        "feedlot_asesor_q_growth",
      ],
    },
    {
      title: t("feedlot_asesor_group_finance"),
      keys: [
        "feedlot_asesor_q_balance",
        "feedlot_asesor_q_feed_cost",
        "feedlot_asesor_q_cost_breakdown",
        "feedlot_asesor_q_expenses",
        "feedlot_asesor_q_margin",
        "feedlot_asesor_q_outstanding",
      ],
    },
    {
      title: t("feedlot_asesor_group_admin"),
      keys: [
        "feedlot_asesor_q_sanitary_pending",
        "feedlot_asesor_q_recent_moves",
        "feedlot_asesor_q_summary",
      ],
    },
  ];

  function csrfHeaders(): Record<string, string> {
    return {
      "Content-Type": "application/json",
      "X-CSRFToken": readCsrfTokenFromCookie(),
    };
  }

  // Lazily open one conversation for this client; reuse it for later turns.
  async function ensureConversation(): Promise<number> {
    if (conversationId !== null) return conversationId;
    const res = await fetch(`${publicBackendUrl}/api/conversations/`, {
      method: "POST",
      credentials: "include",
      headers: csrfHeaders(),
      body: JSON.stringify({
        client: clientId,
        title: `${t("feedlot_module_asesor_title")} · ${clientName}`.trim(),
      }),
    });
    if (!res.ok) throw new Error(`conversation ${res.status}`);
    const data = await res.json();
    conversationId = Number(data.id);
    return conversationId;
  }

  async function ask(question: string): Promise<void> {
    const text = question.trim();
    if (!text || sending || clientId === null) return;
    error = "";
    sending = true;
    turns = [...turns, { role: "user", text }];
    try {
      const id = await ensureConversation();
      const res = await fetch(
        `${publicBackendUrl}/api/conversations/${id}/messages/`,
        {
          method: "POST",
          credentials: "include",
          headers: csrfHeaders(),
          body: JSON.stringify({ text }),
        },
      );
      if (!res.ok) throw new Error(`message ${res.status}`);
      const answer = await res.json();
      turns = [...turns, { role: "assistant", text: String(answer.text ?? "") }];
    } catch {
      error = t("feedlot_asesor_error");
    } finally {
      sending = false;
    }
  }

  function onSubmit(event: Event): void {
    event.preventDefault();
    const q = input;
    input = "";
    ask(q);
  }
</script>

<div class="flex flex-col gap-5">
  <!-- Preset questions -->
  <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
    <h2 class="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
      {t("feedlot_asesor_presets_title")}
    </h2>
    <div class="flex flex-col gap-4">
      {#each groups as group (group.title)}
        <div class="flex flex-col gap-2">
          <div class="text-xs font-semibold uppercase tracking-[0.1em] text-primary">{group.title}</div>
          <div class="flex flex-wrap gap-2">
            {#each group.keys as key (key)}
              <button
                type="button"
                disabled={sending || clientId === null}
                onclick={() => ask(t(key))}
                class="rounded-full px-3 py-1.5 text-left text-xs font-medium transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
                style="border: var(--hairline) solid var(--border); color: var(--foreground);"
              >{t(key)}</button>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  </div>

  <!-- Conversation thread -->
  <div class="rounded-2xl p-5" style="background: var(--card); border: var(--hairline) solid var(--border);">
    <div class="flex flex-col gap-3">
      {#if turns.length === 0}
        <p class="py-6 text-center text-sm text-muted-foreground">{t("feedlot_asesor_empty")}</p>
      {:else}
        {#each turns as turn, i (i)}
          <div class="flex flex-col gap-1 {turn.role === 'user' ? 'items-end' : 'items-start'}">
            <span class="text-[0.65rem] font-semibold uppercase tracking-wide text-muted-foreground">
              {turn.role === "user" ? t("feedlot_asesor_you") : t("feedlot_asesor_advisor")}
            </span>
            <div
              class="max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm"
              style={turn.role === "user"
                ? "background: var(--primary); color: var(--primary-foreground);"
                : "background: var(--muted); color: var(--foreground);"}
            >{turn.text}</div>
          </div>
        {/each}
      {/if}

      {#if sending}
        <div class="flex items-start">
          <div class="rounded-2xl px-4 py-2.5 text-sm text-muted-foreground" style="background: var(--muted);">
            {t("feedlot_asesor_thinking")}
          </div>
        </div>
      {/if}

      {#if error}
        <p class="text-sm text-destructive">{error}</p>
      {/if}
    </div>

    <!-- Free-text ask -->
    <form class="mt-4 flex items-center gap-2" onsubmit={onSubmit}>
      <Input
        type="text"
        bind:value={input}
        disabled={sending || clientId === null}
        placeholder={t("feedlot_asesor_input_placeholder")}
        class="flex-1"
      />
      <Button type="submit" disabled={sending || clientId === null || input.trim() === ""}>
        {t("feedlot_asesor_send")}
      </Button>
    </form>

    <p class="mt-3 text-xs text-muted-foreground">{t("feedlot_asesor_disclaimer")}</p>
  </div>
</div>
