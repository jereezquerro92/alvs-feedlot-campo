/* LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-52-frontend-and-design-system]] · [[adr-15-chatbot-two-tier]]
 * Docs: [[FRONTEND]] · [[CHATBOT]]
 * LIVE-DOC:END */

// The single assembler of ChatUI's rendered copy ([[LOCALIZATION]]). Both
// callers — the /chatui/ page and the shell's ChatDrawer — build their `copy`
// prop here rather than each hand-listing the same keys, which is how the two
// surfaces drift apart. Every string resolves through `t(...)`; the component
// itself stays locale-agnostic and receives text, never keys.
//
// `outcomeCopy` is keyed on the message keys `copyForResult` returns
// ($lib/router-client), so the frontend owns every non-Action string — the
// router response carries no prose beyond the registry-authored label
// ([[CHATBOT]] "The action descriptor", adr-15 rule 5).

import { t } from "../i18n";

export interface ChatUICopy {
  title: string;
  emptyState: string;
  composerPlaceholder: string;
  composerAriaLabel: string;
  composerSend: string;
  composerPlaceholderExamples?: string[];
  messageGo: string;
  messageConfirm: string;
  outcomeCopy: Record<string, string>;
}

export function routerChatCopy(): ChatUICopy {
  return {
    title: t("chatui_router_title"),
    emptyState: t("chatui_router_empty"),
    composerPlaceholder: t("chatui_composer_placeholder"),
    composerAriaLabel: t("chatui_composer_aria_label"),
    composerSend: t("chatui_composer_send"),
    composerPlaceholderExamples: [
      t("chatui_composer_placeholder_example_1"),
      t("chatui_composer_placeholder_example_2"),
      t("chatui_composer_placeholder_example_3"),
    ],
    messageGo: t("chatui_message_go"),
    messageConfirm: t("chatui_message_confirm"),
    outcomeCopy: {
      router_outcome_escalate: t("router_outcome_escalate"),
      router_outcome_no_match: t("router_outcome_no_match"),
      router_outcome_disabled: t("router_outcome_disabled"),
      router_outcome_hard_reject: t("router_outcome_hard_reject"),
      router_outcome_throttled: t("router_outcome_throttled"),
      router_outcome_network_error: t("router_outcome_network_error"),
    },
  };
}
