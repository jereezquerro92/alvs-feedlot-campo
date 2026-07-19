/* LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
 * Governed by: [[adr-04-frontend-and-design-system]]
 * Docs: [[FRONTEND]]
 * LIVE-DOC:END */

// Plain, DOM-free client for POST /api/router/route/ ([[API]], [[CHATBOT]]),
// extracted so the request shape and outcome dispatch are unit-testable
// without a jsdom/SSR harness ([[FRONTEND]] test conventions: bun:test only).

export interface RouterAction {
  kind: "navigate" | "confirm";
  target: string;
  label: string;
}

export type RouterOutcome =
  | { outcome: "Action"; query_id: string; action: RouterAction }
  | { outcome: "Escalate"; query_id: string }
  | { outcome: "NO_MATCH"; query_id: string }
  | { outcome: "disabled"; query_id: string };

export type RouteResult =
  | { kind: "outcome"; data: RouterOutcome }
  | { kind: "hard_reject" }
  | { kind: "throttled" }
  | { kind: "network_error" };

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

/**
 * POSTs `utterance` to `${backendUrl}/api/router/route/` with the session
 * cookie and CSRF token, and classifies the response into a `RouteResult`.
 * `csrfToken` is read by the caller (readCsrfTokenFromCookie in $lib/csrf)
 * so this module stays DOM-free and fetch-injectable for tests.
 */
export async function routeUtterance(
  backendUrl: string,
  utterance: string,
  csrfToken: string,
  fetchImpl: FetchLike = fetch,
): Promise<RouteResult> {
  try {
    const res = await fetchImpl(`${backendUrl}/api/router/route/`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({ utterance }),
    });

    if (res.status === 422) return { kind: "hard_reject" };
    if (res.status === 429) return { kind: "throttled" };
    if (!res.ok) return { kind: "network_error" };

    const data = (await res.json()) as RouterOutcome;
    return { kind: "outcome", data };
  } catch {
    return { kind: "network_error" };
  }
}

// Frontend-owned outcome-to-message-key mapping — the backend sends only the
// outcome key, never prose (adr-15 rule 5). Values are `MessageKey`s from
// the i18n layer ([[LOCALIZATION]]); the caller resolves the actual copy via
// `t(key)` so this module stays locale-agnostic and DOM-free.
export const OUTCOME_COPY: Record<string, string> = {
  Escalate: "router_outcome_escalate",
  NO_MATCH: "router_outcome_no_match",
  disabled: "router_outcome_disabled",
  hard_reject: "router_outcome_hard_reject",
  throttled: "router_outcome_throttled",
  network_error: "router_outcome_network_error",
};

/** Resolves the message key to render for a completed RouteResult, or null for an Action outcome. */
export function copyForResult(result: RouteResult): string | null {
  if (result.kind !== "outcome") return OUTCOME_COPY[result.kind];
  if (result.data.outcome === "Action") return null;
  return OUTCOME_COPY[result.data.outcome] ?? OUTCOME_COPY.network_error;
}
