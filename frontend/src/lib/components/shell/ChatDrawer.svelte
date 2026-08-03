<!-- LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
     Governed by: [[adr-52-frontend-and-design-system]] · [[adr-15-chatbot-two-tier]] · [[adr-22-showcase-ready-components]]
     Docs: [[FRONTEND]] · [[DESIGN-SYSTEM]] · [[CHATBOT]] · [[COMPONENTIZATION]]
     LIVE-DOC:END -->

<!--
  Composition only: overlay/Drawer + chat/ChatUI, docked to the right edge on
  every gated page ([[CHATBOT]]). It is the SAME router surface /chatui/ hosts
  — the tier that chooses, posting to POST /api/router/route/ ([[API]]) and
  rendering only the closed enum that comes back. No second component, no
  generating tier, no page context in the request (adr-15 rules 1 and 5).

  The Drawer owns the header, so ChatUI is mounted with `heading={false}` and
  the page keeps exactly one `h1`. A zero-prop mount renders a collapsed,
  empty-copy drawer and performs nothing (adr-22 rules 1 and 4) — the thread
  is client-local state and no request leaves until the user submits.
-->
<script lang="ts">
  import Drawer from "$lib/components/overlay/Drawer.svelte";
  import ChatUI from "$lib/components/chat/ChatUI.svelte";
  import { t } from "../../../i18n";
  import type { ChatUICopy } from "$lib/chatui-copy";

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
    publicBackendUrl = "",
    copy = EMPTY_COPY,
    open = $bindable(false),
  }: {
    publicBackendUrl?: string;
    /** Built by `routerChatCopy()` in the layout ([[LOCALIZATION]]). */
    copy?: ChatUICopy;
    open?: boolean;
  } = $props();
</script>

<Drawer
  bind:open
  side="right"
  width="24rem"
  title={copy.title || t("chatui_router_title")}
  openLabel={t("shell_chat_drawer_open")}
  closeLabel={t("shell_chat_drawer_close")}
>
  <div class="flex h-full min-h-0 flex-col">
    <ChatUI
      heading={false}
      {publicBackendUrl}
      {copy}
      class="max-w-none px-0 py-0"
    />
  </div>
</Drawer>
