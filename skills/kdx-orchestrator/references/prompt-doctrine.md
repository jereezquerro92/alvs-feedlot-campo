# Prompt Doctrine: WHAT not HOW

The orchestrator's biggest token sink — and biggest source of fragile dispatches — is over-specified prompts. A prompt that dictates `curl`/`jq`/`sudo` step-by-step:

1. **Pays twice** — the orchestrator already reasoned through the steps, then the worker re-reads them. Double input tokens for the same plan.
2. **Demotes the worker** from reasoner to parrot. No adaptation when a prescribed command returns an unexpected shape.
3. **Drifts under change** — literal commands rot (API version, flag name, file path). The intent doesn't.

## The contract, not the script

Hand the worker a **contract**, not a playbook:

| Field | Purpose |
|---|---|
| Objective | The outcome in 1–2 lines. *Not* the activity. |
| Constraints | What NOT to do. Secrets, idempotency, scope, side effects to avoid. |
| Acceptance criteria | A check the worker (and you) can run to know it's done. |
| Output schema | YAML frontmatter fields beyond the mandatory `status:` + `resolution:`. |
| Discovered context | Facts only: IDs, paths, URLs, prior decisions. Never the command that discovered them. |

## Forbidden in dispatch prompts

- Bash code blocks
- Literal commands: `curl …`, `jq …`, `sudo …`, `openssl …`, `systemctl …`, `git …`, `python3 -c …`
- Numbered step playbooks ("1. Do X. 2. Then Y. 3. Verify Z.")
- Conditional logic in prose (`if … then …`, `si retorna 401 entonces …`)
- Tool-choice prescriptions ("use Python not bash") — those live in CLAUDE.md when they apply project-wide

## Required in dispatch prompts

- Objective stated as outcome
- Constraints stated as rules (`MUST NOT log …`, `MUST be idempotent`, `MUST survive reboot`)
- Acceptance criteria expressed as observable checks ("returns 404 not 530", "shows `Registered tunnel connection` in logs")
- Discovered context as bare facts ("Account ID: …", "Zone: …", "Token at /path/…, may be expired")

## Size budget

Dispatch prompt ≤ ~40 lines. If you've written a 200-line playbook, you've written the script instead of the contract — the worker can only echo. Trust the tier: `orch-medium` (Sonnet) and `orch-high` (Opus) can plan; `orch-low` (Haiku) is for narrow, well-defined lookups.

## Before / After

### Before — parroting (the antipattern)

```
## Task
Migrate cloudflared.service to a Named Tunnel. Plan:
1. Read token: python3 -c "import tomllib; d=tomllib.loads(open('…').read()); print(d['oauth_token'])"
2. curl -sS -H "Authorization: Bearer $TOKEN" https://api.cloudflare.com/client/v4/user/tokens/verify
3. If returns 401: wrangler whoami; reread token; retry
4. curl -sS -H "Authorization: Bearer $TOKEN" 'https://api.cloudflare.com/.../zones?name=kodexarg.com' | jq -r '.result[0].id'
5. SECRET=$(openssl rand -base64 32); curl -X POST … /cfd_tunnel -d '{"name":"kdx-pc-ssh", …}'
6. If REC_ID = null: POST /dns_records; else PUT /dns_records/$REC_ID
7. echo -n "$CONNECTOR_TOKEN" | sudo tee /etc/cloudflared/kdx-pc-ssh.token
…
```

The worker is transcribing, not deciding. If step 4 returns an empty array, the prompt has no recovery. Every `curl` flag was reasoned by the orchestrator and re-reasoned by the worker.

### After — intent-based (the doctrine)

```
## Task

Migrate `cloudflared.service` from anonymous Quick Tunnel to a Named Tunnel
that serves `ssh.kodexarg.com` → `ssh://localhost:22`.

### Constraints

- Unattended (no interactive prompts).
- Never log, print, or commit: oauth_token, connector_token, tunnel_secret.
  Redact past first 8 chars if shown for debugging.
- Idempotent: if a `kdx-pc-ssh` tunnel with no active connections already
  exists, replace it. Do not accumulate orphans.
- systemd unit must restart cleanly and survive reboot.

### Acceptance criteria

- `systemctl is-active cloudflared.service` returns `active`
- `https://ssh.kodexarg.com/` returns HTTP 404 (catch-all ingress),
  NOT 530 (tunnel offline)
- cloudflared logs show `Registered tunnel connection` within 30s of restart

### Discovered context (facts)

- Account ID: 15604caa33d6f430bd34a1861ed37483
- Zone: kodexarg.com
- Wrangler OAuth token at ~/.config/.wrangler/config/default.toml
  (field `oauth_token`; may be expired — refresh path exists)
- DNS `ssh.kodexarg.com` already a CNAME to an orphan tunnel UUID
- cloudflared binary: /usr/local/bin/cloudflared (v2026.3.0)
- sudo passwordless for user `kodex`

### Output schema

Standard frontmatter + `tunnel_id: <uuid>` (public, not secret).
Body: what changed, final HTTP code, last 5 cloudflared log lines.
Never include token values, even truncated.
```

The worker now owns: tool choice (curl vs wrangler vs SDK), error branches, retry logic, ordering, file permissions strategy. It **reasons** — that's why you spawned it.

## Self-check before dispatching

Ask three questions:

1. *If the first thing the worker tries fails, can it adapt with what I gave it?*
2. *Have I named a tool the worker didn't need to be told to use?*
3. *Could I delete every fenced code block and lose only convenience, not meaning?*

Expected answers: **yes / no / yes**. Anything else → rewrite. The contract is in the constraints and acceptance criteria, not in the steps.

## Special cases

- **Hard requirement to use a specific command**: state it as a constraint (`MUST use systemctl, not service`) — one line, no embedded flags. The worker still chooses arguments.
- **Reusing a literal value** (an exact path, an exact env var name, an exact endpoint): that's a fact, not a command. Quote the value, not the invocation.
- **Multi-step pipelines where order is load-bearing**: state the ordering constraint (`DNS record must point at the tunnel UUID before the systemd unit is restarted`) — let the worker pick the operations.

## References

- Augment Code — *Multi-Agent Orchestration Architecture Guide* (2026): coordination failures account for ~37% of multi-agent failure modes; root cause is shared-context drift.
- Anthropic — *Building Agents with the Claude Agent SDK* (2026): verify-iterate loops over step prescription; subagents own execution.
- Pathmode — *Orchestration Era Needs Intent* (2026): intent specs (objective + constraints + verification) replace prescriptive delegation.
- Microsoft — *Conductor: Deterministic Orchestration for Multi-Agent AI Workflows* (May 2026): workflows expressed as goals + conditions, never imperative shell.
