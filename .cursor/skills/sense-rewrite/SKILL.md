---
name: sense-rewrite
description: >-
  Prefaces the reply with blockquoted native American English rewrites, then a
  horizontal rule, then the real answer. Use ONLY when the user message has
  Spanish that must be translated to act, or English that could be understood
  two different ways and that ambiguity would change the task. Do not use for
  trivial typos that leave meaning clear. Skip when kdx-triage already owns the
  turn (its Step 1 restatement covers it).
---

# sense-rewrite

## When (hard gate)

Fire **only** if either is true:

1. **Spanish** in the user message that you must translate to act.
2. **Sense risk** — a wording that could be understood differently and would change the task or communication.

Otherwise do nothing. Do not polish clear English.

## Format (when firing)

Any misspell, any word incorrectly used, any paragraph that doesn't sound native american english and could change the sense, the communication, must be:

1) rewritten, in a quote >
2) draw a line and continue the answer.

Concrete shape:

```
> <corrected native American English>

---

<normal answer>
```

One `>` line per corrected span. Then exactly one `---`. Then continue.

## Coexistence

- **`kdx-triage` owns the turn** → skip; triage Step 1 already restates in English.
- Code/docs language rules stay with [[LOCALIZATION]] — this skill is chat-only.
