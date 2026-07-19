import { describe, expect, test } from "bun:test";
import { copyForResult, OUTCOME_COPY, routeUtterance, type FetchLike } from "../src/lib/router-client";

// Unit coverage for the router-client used by the chat surface ([[CHATBOT]],
// bdd-04): asserts the POST shape (endpoint, credentials, CSRF header, JSON
// body) and that every backend outcome — Action/navigate, Action/confirm,
// Escalate, NO_MATCH, disabled, plus the 422/429/network error paths — maps
// to the correct RouteResult, never leaking raw backend prose. DOM-free per
// this template's bun:test conventions (no jsdom).

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("routeUtterance", () => {
  test("POSTs to /api/router/route/ with credentials, CSRF header, and JSON body", async () => {
    let capturedUrl = "";
    let capturedInit: RequestInit | undefined;
    const fetchImpl: FetchLike = async (url, init) => {
      capturedUrl = url;
      capturedInit = init;
      return jsonResponse({ outcome: "NO_MATCH", query_id: "q1" });
    };

    await routeUtterance("http://localhost:8000", "open dashboard", "csrf-token-123", fetchImpl);

    expect(capturedUrl).toBe("http://localhost:8000/api/router/route/");
    expect(capturedInit?.method).toBe("POST");
    expect(capturedInit?.credentials).toBe("include");
    const headers = capturedInit?.headers as Record<string, string>;
    expect(headers["X-CSRFToken"]).toBe("csrf-token-123");
    expect(headers["Content-Type"]).toBe("application/json");
    expect(JSON.parse(capturedInit?.body as string)).toEqual({ utterance: "open dashboard" });
  });

  test("Action/navigate outcome is returned untouched for the caller to act on", async () => {
    const fetchImpl: FetchLike = async () =>
      jsonResponse({
        outcome: "Action",
        query_id: "q1",
        action: { kind: "navigate", target: "/dashboard/", label: "Open dashboard" },
      });

    const result = await routeUtterance("http://localhost:8000", "go to dashboard", "csrf", fetchImpl);

    expect(result.kind).toBe("outcome");
    if (result.kind !== "outcome") throw new Error("unreachable");
    expect(result.data.outcome).toBe("Action");
    if (result.data.outcome !== "Action") throw new Error("unreachable");
    expect(result.data.action.kind).toBe("navigate");
    expect(result.data.action.target).toBe("/dashboard/");
    expect(copyForResult(result)).toBeNull();
  });

  test("Action/confirm outcome carries the registry label for the confirm affordance", async () => {
    const fetchImpl: FetchLike = async () =>
      jsonResponse({
        outcome: "Action",
        query_id: "q2",
        action: { kind: "confirm", target: "/actions/delete-report/", label: "Delete the report?" },
      });

    const result = await routeUtterance("http://localhost:8000", "delete the report", "csrf", fetchImpl);

    expect(result.kind).toBe("outcome");
    if (result.kind !== "outcome") throw new Error("unreachable");
    expect(result.data.outcome).toBe("Action");
    if (result.data.outcome !== "Action") throw new Error("unreachable");
    expect(result.data.action.kind).toBe("confirm");
    expect(result.data.action.label).toBe("Delete the report?");
  });

  for (const outcome of ["Escalate", "NO_MATCH", "disabled"] as const) {
    test(`${outcome} outcome maps to its own localized copy, never raw backend text`, async () => {
      const fetchImpl: FetchLike = async () => jsonResponse({ outcome, query_id: "q3" });
      const result = await routeUtterance("http://localhost:8000", "whatever", "csrf", fetchImpl);
      expect(copyForResult(result)).toBe(OUTCOME_COPY[outcome]);
    });
  }

  test("422 hard reject maps to a non-alarming localized copy", async () => {
    const fetchImpl: FetchLike = async () => new Response(JSON.stringify({ detail: "router_hard_reject" }), { status: 422 });
    const result = await routeUtterance("http://localhost:8000", "garbage", "csrf", fetchImpl);
    expect(result.kind).toBe("hard_reject");
    expect(copyForResult(result)).toBe(OUTCOME_COPY.hard_reject);
  });

  test("429 throttle maps to its own localized copy", async () => {
    const fetchImpl: FetchLike = async () => new Response(null, { status: 429 });
    const result = await routeUtterance("http://localhost:8000", "spam", "csrf", fetchImpl);
    expect(result.kind).toBe("throttled");
    expect(copyForResult(result)).toBe(OUTCOME_COPY.throttled);
  });

  test("network failure maps to a network_error copy", async () => {
    const fetchImpl: FetchLike = async () => {
      throw new Error("connection refused");
    };
    const result = await routeUtterance("http://localhost:8000", "hello", "csrf", fetchImpl);
    expect(result.kind).toBe("network_error");
    expect(copyForResult(result)).toBe(OUTCOME_COPY.network_error);
  });

  test("an unexpected non-ok status without a specific branch also maps to network_error", async () => {
    const fetchImpl: FetchLike = async () => new Response(null, { status: 500 });
    const result = await routeUtterance("http://localhost:8000", "hello", "csrf", fetchImpl);
    expect(result.kind).toBe("network_error");
  });
});
