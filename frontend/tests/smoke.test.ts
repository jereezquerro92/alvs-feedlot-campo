import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { t } from "../src/i18n";
import { DENIED_REDIRECT } from "../src/lib/authGate";

// Smoke tests for the SSR routes ([[FRONTEND]] T5): / renders a Showcase
// button and a Card carrying the two backend words (bdd-01); /showcase/components/
// and /healthz respond 200; each carries an explicit Cache-Control. Runs
// against the built standalone server (`bun run build` first). No backend is
// required — no cookie is sent, so /showcase/components/ renders the
// anonymous auth section without a live /api/me/ call; / tolerates either a
// live backend or its per-word error-code fallback.
//
// bdd-02: the / session badge (avatar + display name / "Log in") is covered
// by a second describe block below, each with its own SSR server instance
// pointed at a stub /api/me/ backend (Bun.serve) — BACKEND_API_URL is read
// once per server process, so the authenticated and anonymous branches need
// separate processes to exercise both without a live Cognito dependency.
//
// bdd-07: the site-wide melt dark theme default. With no `theme` cookie,
// every route renders `<html class="dark" data-bg-preset="melt">` — proven
// here for `/` without a browser/computed-style layer.
//
// bdd-08 / adr-20: the authorization lobby. Every route but `/` requires
// a Group-holding session — a role-less (`groups: []`) session is confined
// to `/`, where it sees the `lobby_pending` legend instead of the nav/M365
// content. An anonymous visitor is likewise redirected to `/` from every
// other route (no cookie is sent, so no backend call is even attempted —
// the guard short-circuits deterministically without a live backend). The
// role-holding (`groups: ["admins"]`) 200 variants live in the stub-backed
// describe block below, alongside the pending-redirect variants.

const PORT = 43217;
const BASE = `http://127.0.0.1:${PORT}`;
let server: ReturnType<typeof Bun.spawn>;

async function waitForServer(timeoutMs = 20000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${BASE}/healthz`);
      if (res.ok) return;
    } catch {
      // not up yet
    }
    await Bun.sleep(200);
  }
  throw new Error("SSR server did not start in time");
}

beforeAll(async () => {
  const entry = new URL("../dist/server/entry.mjs", import.meta.url).pathname;
  if (!(await Bun.file(entry).exists())) {
    throw new Error(`missing ${entry} — run \`bun run build\` before \`bun test\``);
  }
  server = Bun.spawn(["bun", entry], {
    env: { ...process.env, HOST: "127.0.0.1", PORT: String(PORT) },
    stdout: "pipe",
    stderr: "pipe",
  });
  await waitForServer();
});

afterAll(() => {
  server?.kill();
});

test("/ renders a Showcase button, with an explicit Cache-Control, and hides the M365 status card from an anonymous visitor (issue #246)", async () => {
  const res = await fetch(`${BASE}/`, { redirect: "manual" });
  expect(res.status).toBe(200);
  expect(res.headers.get("cache-control")).toBeTruthy();
  const body = await res.text();
  expect(body).toContain('href="/showcase/components/"');
  // The M365 status card (two <span class="text-sm"> word slots) is gated
  // behind an authenticated session on the frontend, even though
  // adr-13-m365-graph rule 3 leaves its backend routes AllowAny. The exact
  // class excludes SessionBadge's differently-classed username span.
  expect((body.match(/<span class="text-sm">/g) ?? []).length).toBe(0);
});

test("/ with no theme cookie renders the flipped defaults on <html> — dark mode + melt background (docs/bdds/bdd-07-melt-theme-sitewide.md)", async () => {
  const res = await fetch(`${BASE}/`);
  expect(res.status).toBe(200);
  const body = await res.text();
  expect(body).toContain('<html lang="en" class="dark" data-bg-preset="melt"');
});

test("/ with no session cookie renders the anonymous Log in affordance (bdd-02)", async () => {
  const res = await fetch(`${BASE}/`);
  expect(res.status).toBe(200);
  const body = await res.text();
  expect(body).toContain(t("auth_login"));
  expect(body).toContain("/accounts/login/");
});

test("/showcase/components/ redirects an anonymous visitor to / (bdd-08, adr-20 lobby)", async () => {
  const res = await fetch(`${BASE}/showcase/components/`, { redirect: "manual" });
  expect(res.status).toBe(302);
  expect(res.headers.get("location")).toBe(DENIED_REDIRECT);
});

test("/chatui/ redirects an anonymous visitor to / (bdd-08, adr-20 lobby)", async () => {
  const res = await fetch(`${BASE}/chatui/`, { redirect: "manual" });
  expect(res.status).toBe(302);
  expect(res.headers.get("location")).toBe(DENIED_REDIRECT);
});

test("/profile/ redirects an anonymous visitor to / (bdd-08, adr-20 lobby)", async () => {
  const res = await fetch(`${BASE}/profile/`, { redirect: "manual" });
  expect(res.status).toBe(302);
  expect(res.headers.get("location")).toBe(DENIED_REDIRECT);
});

test("/healthz returns 200 with explicit Cache-Control", async () => {
  const res = await fetch(`${BASE}/healthz`);
  expect(res.status).toBe(200);
  expect(res.headers.get("cache-control")).toBe("no-store");
  expect(await res.json()).toEqual({ status: "ok" });
});

test("404 on an undeclared route still carries an explicit Cache-Control (issue #52)", async () => {
  // Per-page Cache-Control (the pattern above) cannot cover a framework-
  // generated response — the default 404 never runs any page's frontmatter
  // (adr-06 rule 3: absent header is a bug, frontend-container counterpart
  // of the backend's #46). The backstop is src/middleware.ts.
  const res = await fetch(`${BASE}/nope-404/`);
  expect(res.status).toBe(404);
  expect(res.headers.get("cache-control")).toBeTruthy();
});

describe("/ session badge, authenticated branch (bdd-02); lobby gating (bdd-08, adr-20)", () => {
  const STUB_PORT = 43218;
  const SSR_PORT = 43219;
  const SSR_BASE = `http://127.0.0.1:${SSR_PORT}`;
  let stub: ReturnType<typeof Bun.serve>;
  let ssrServer: ReturnType<typeof Bun.spawn>;

  beforeAll(async () => {
    stub = Bun.serve({
      port: STUB_PORT,
      fetch(req) {
        if (new URL(req.url).pathname === "/api/me/") {
          // The SSR fetch forwards the request's cookie header verbatim, so
          // the stub branches on it to serve the empty-picture, non-empty-
          // picture, and role-holding cases from one server without extra
          // spawns. "stub-role" -> groups: ["admins"] (authorized); any
          // other "stub*" cookie -> groups: [] (pending).
          const cookie = req.headers.get("cookie") ?? "";
          const picture = cookie.includes("stub-picture")
            ? "https://example.com/avatar.png"
            : "";
          const groups = cookie.includes("stub-role") ? ["admins"] : [];
          return Response.json({
            sub: "stub-sub",
            email: "stub@example.com",
            given_name: "Stub",
            family_name: "User",
            picture,
            groups,
            nickname: "",
            avatar_visible: true,
          });
        }
        return new Response("not found", { status: 404 });
      },
    });

    const entry = new URL("../dist/server/entry.mjs", import.meta.url).pathname;
    ssrServer = Bun.spawn(["bun", entry], {
      env: {
        ...process.env,
        HOST: "127.0.0.1",
        PORT: String(SSR_PORT),
        BACKEND_API_URL: `http://127.0.0.1:${STUB_PORT}`,
      },
      stdout: "pipe",
      stderr: "pipe",
    });

    const deadline = Date.now() + 20000;
    while (Date.now() < deadline) {
      try {
        const res = await fetch(`${SSR_BASE}/healthz`);
        if (res.ok) break;
      } catch {
        // not up yet
      }
      await Bun.sleep(200);
    }
  });

  afterAll(() => {
    ssrServer?.kill();
    stub?.stop();
  });

  test("with a session cookie and a stub backend returning 200, renders the avatar, display name, and logout form, not Log in", async () => {
    const res = await fetch(`${SSR_BASE}/`, {
      headers: { cookie: "sessionid=stub" },
    });
    expect(res.status).toBe(200);
    const body = await res.text();
    // The stub carries no nickname, so the pill derives "given family"
    // (issue #276); the popover still anchors on the full address.
    expect(body).toContain("Stub User");
    expect(body).toContain("stub@example.com");
    // The login label rides serialized island props even on the
    // authenticated branch — probe the rendered login LINK instead.
    expect(body).not.toContain("/accounts/login/");
    expect(body).toContain('action="http://localhost:8000/accounts/logout/"');
    expect(body).toContain('name="csrfmiddlewaretoken"');
  });

  test("with a session cookie and zero groups (pending), the lobby legend renders and the nav buttons + M365 Card are hidden (bdd-08)", async () => {
    const res = await fetch(`${SSR_BASE}/`, {
      headers: { cookie: "sessionid=stub" },
    });
    expect(res.status).toBe(200);
    const body = await res.text();
    expect(body).toContain(t("lobby_pending"));
    expect(body).not.toContain('href="/showcase/components/"');
    expect(body).not.toContain('href="/profile/"');
    expect((body.match(/<span class="text-sm">/g) ?? []).length).toBe(0);
  });

  test("with a session cookie and a role-holding group (groups: [admins]), the nav buttons + M365 Card render, no legend (bdd-08)", async () => {
    const res = await fetch(`${SSR_BASE}/`, {
      headers: { cookie: "sessionid=stub-role" },
    });
    expect(res.status).toBe(200);
    const body = await res.text();
    expect(body).toContain('href="/showcase/components/"');
    expect((body.match(/<span class="text-sm">/g) ?? []).length).toBe(2);
    expect(body).not.toContain(t("lobby_pending"));
    // The profile deep-link lives inside SessionBadge's ☰ popover, gated on
    // the role-holding (non-pending) session.
    expect(body).toContain('href="/profile/"');
  });

  test("with a non-empty picture claim, renders an <img> with that src, not the initials fallback", async () => {
    const res = await fetch(`${SSR_BASE}/`, {
      headers: { cookie: "sessionid=stub-picture" },
    });
    expect(res.status).toBe(200);
    const body = await res.text();
    expect(body).toContain('src="https://example.com/avatar.png"');
    expect(body).toMatch(/<img[^>]*src="https:\/\/example\.com\/avatar\.png"/);
    // Initials fallback ("SU" from Stub/User) must not render alongside the image.
    expect(body).not.toContain(">SU<");
  });

  test("without a cookie against the same server, still falls back to Log in", async () => {
    const res = await fetch(`${SSR_BASE}/`);
    expect(res.status).toBe(200);
    const body = await res.text();
    expect(body).toContain(t("auth_login"));
  });

  test("/showcase/components/ redirects a role-less (pending) session to / (bdd-08, adr-20)", async () => {
    const res = await fetch(`${SSR_BASE}/showcase/components/`, {
      headers: { cookie: "sessionid=stub" },
      redirect: "manual",
    });
    expect(res.status).toBe(302);
    expect(res.headers.get("location")).toBe(DENIED_REDIRECT);
  });

  test("/showcase/components/ returns 200 for a role-holding session, with the design-system gallery and its DataTable/Dialog/ThemeModeToggle markers", async () => {
    const res = await fetch(`${SSR_BASE}/showcase/components/`, {
      headers: { cookie: "sessionid=stub-role" },
    });
    expect(res.status).toBe(200);
    expect(res.headers.get("cache-control")).toBe("no-store");
    const body = await res.text();
    expect(body).toContain("Secondary");
    expect(body).toContain(t("gallery_datatable"));
    expect(body).toContain(t("demo_dialog_trigger"));
    expect(body).toContain(t("demo_summary_title"));
    expect(body).toContain(t("demo_dropdown_trigger"));
    expect(body).toContain(t("demo_dropdown_edit"));
    expect(body).toContain(t("demo_popover_trigger"));
    expect(body).toContain(t("demo_popover_quote"));
    expect(body).toContain("&quot;name&quot;:&quot;ThemeModeToggle&quot;");
  });

  test("/chatui/ redirects a role-less (pending) session to / (bdd-08, adr-20)", async () => {
    const res = await fetch(`${SSR_BASE}/chatui/`, {
      headers: { cookie: "sessionid=stub" },
      redirect: "manual",
    });
    expect(res.status).toBe(302);
    expect(res.headers.get("location")).toBe(DENIED_REDIRECT);
  });

  test("/chatui/ returns 200 for a role-holding session", async () => {
    const res = await fetch(`${SSR_BASE}/chatui/`, {
      headers: { cookie: "sessionid=stub-role" },
    });
    expect(res.status).toBe(200);
    expect(res.headers.get("cache-control")).toBe("no-store");
  });

  test("/profile/ redirects a role-less (pending) session to / (bdd-08, adr-20)", async () => {
    const res = await fetch(`${SSR_BASE}/profile/`, {
      headers: { cookie: "sessionid=stub" },
      redirect: "manual",
    });
    expect(res.status).toBe(302);
    expect(res.headers.get("location")).toBe(DENIED_REDIRECT);
  });

  test("/profile/ returns 200 for a role-holding session", async () => {
    const res = await fetch(`${SSR_BASE}/profile/`, {
      headers: { cookie: "sessionid=stub-role" },
    });
    expect(res.status).toBe(200);
    expect(res.headers.get("cache-control")).toBe("no-store");
  });
});
