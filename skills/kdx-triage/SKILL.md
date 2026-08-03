---
name: kdx-triage
description: Cheap, fast triage of an idea or proposed change BEFORE committing real tokens. Restates the idea in English, scouts read-only with parallel haiku workers (orch-low), and returns a fixed Spanish verdict card — one paragraph, affected skills, and a 1-3 matrix (Severidad / Colateral / Esfuerzo) drawn with ●○ icons. Use when kodex says "triage", "triagealo", "evaluá esta idea", "qué tan grave / riesgoso / caro es", "vale la pena?", or pitches a change and wants a quick go/no-go read instead of an implementation.
---

# kdx-triage

Mini-orchestrator that turns a raw idea into a one-glance verdict card.
It NEVER implements anything — read-only scouting, then a scored matrix.
Skill body and reasoning in English; the final card is always in Spanish.

## Contract

- Input: an idea, proposal, or complaint (any language, any quality).
- Output: exactly the card in **Output format** below. Nothing else.
- No file writes, no fixes, no "while I'm here" improvements.
- Total spend target: 2–3 haiku scouts + one synthesis in the main context.

## Step 1 — Restate (always, visibly)

Normalize the idea into one precise English sentence and open the response with:

> The user proposes: <normalized English restatement>

Do this even if a hook already echoed a cleaned prompt — the point is that
kodex can verify in one line that the instruction was understood before any
scouting cost is paid. If the restatement is materially uncertain, say so in
one extra line; do not silently guess.

## Step 2 — Scout (parallel, haiku, read-only)

Dispatch `orch-low` subagents — all in ONE message so they run concurrently.
Pick only the relevant lanes, max 3:

1. **Estate** — `~/Skills/`, `~/Agents/`, `~/.claude/plugins/`, installed plugins:
   which skills/subagents overlap with, duplicate, or would be touched by the idea.
2. **Target** — the repo/files the idea points at (resolve `~/Dev/` aliases;
   scouts read only, so the no-touch rule holds).
3. **Precedent** — `~/Documents/System/System.md`, `~/Documents/System/ADRs/`,
   and vault notes: standing decisions that already settle or constrain the idea.

Each scout returns its standard YAML frontmatter + findings. No prose reports.

## Step 3 — Score the matrix

Read the scout returns and score each axis 1–3:

| Axis | 1 (●○○) | 2 (●●○) | 3 (●●●) |
|---|---|---|---|
| **Severidad** — how much the problem hurts today | cosmetic / nice-to-have | real recurring friction | broken, blocking, or data at risk |
| **Colateral** — blast radius of implementing it | isolated, new files only | shared components, few consumers | shared state, many consumers, machine-wide config, or other agents (agy/grok/hermes) |
| **Esfuerzo** — time + tokens + model tier required | mechanical; haiku/sonnet one pass | sonnet with iteration and tests | opus-level judgment, multi-session, or wide refactor |

Model tier is part of Esfuerzo by definition: if the fix demands opus, it is
never a 1, however small the diff.

## Output format (fixed, Spanish)

```
The user proposes: <English restatement>

## Implementación propuesta
> <párrafo breve en español de qué se pretende hacer>

**Skills afectados:** [skill-a, skill-b]

Severidad  ●●○
Colateral  ●●●
Esfuerzo   ●○○

**Veredicto:** <una línea>
```

- Icons: `●` filled, `○` empty, always three per row, monospace block.
  (Emoji variant `🟠🟠⚪` only when the card is sent to Telegram/phone.)
- `Skills afectados` lists real skill/subagent names found by the Estate scout;
  use `**Áreas afectadas:**` with paths/components when no skills are involved.
- `Veredicto` is derived from the pattern, one line, e.g.: "proceder barato,
  sonnet alcanza", "requiere opus — plantear como sesión propia", "no tocar:
  colateral 3 sobre config compartida", "ya cubierto por <skill> — no crear".
