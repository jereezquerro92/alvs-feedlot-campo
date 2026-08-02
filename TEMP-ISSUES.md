# TEMP-ISSUES — audit board (2026-08-02)

47 issues filed at **[jereezquerro92/alvs-feedlot-campo](https://github.com/jereezquerro92/alvs-feedlot-campo/issues)**, numbered 1–47.
Source: automated 10-area bug hunt over commit `a663d7f`. Each issue body carries a YAML
frontmatter block (`challenge`, `severity`, `confidence`, `related`, `files`) plus
`## What` / `## Failure scenario` / `## Fix sketch` / `## Provenance`.

**Legend** — severity `🔴 critical · 🟠 high · 🟡 medium · ⚪ low` · effort `○ trivial · ◔ low · ◑ medium` · `~` medium confidence, `?` low confidence

Totals: 🔴 5 · 🟠 11 · 🟡 12 · ⚪ 19 — labels: bug 32 · chore 6 · docs 4 · infra 3 · feat 2

---

## 💸 Numeric validation missing before ledger postings — 4

The single biggest cluster. Entity-state checks are rigorous everywhere; number sanity was never on the checklist.

- `🔴 ◔` **#1** `register_payment` accepts negative/zero — a "payment" inflates the debt
- `🔴 ◔` **#3** `register_feeding`/`register_delivery` accept negative qty & price — flips ledger sign
- `🟠 ◔` **#27** `register_field_task`/`register_maintenance` post a debit with no positivity check
- `⚪ ◔~` **#20** market parsers truncate `head_count`, neither rejects a negative price

## 📊 The honest-null contract, breached at three layers — 3

adr-29 rule 2 is the most distinctive doctrine in the project. It drifts independently at metric, contract and render.

- `🔴 ◔` **#2** client-level `conversion()` returns filler zero — its own per-pen descendant has the guard
- `🟡 ◔~` **#16** `LotBars` collapses `null` and genuine zero into one dropped bucket
- `⚪ ○` **#15** `caravana_coverage` returns `None` where the shared contract says `""`

## 🔑 Authorization & tenant isolation — 3

- `🔴 ◑` **#4** revoking `AccessRequest.role` never removes the prior Django Group
- `⚪ ◔~` **#33** `AssistantAccess` doesn't fail closed on a missing/unparseable client
- `⚪ ○~` **#8** ledger viewsets lean on an optional `?client=` with no enforced scoping

## 🐄 Livestock & lot counter integrity — 5

- `🔴 ◑` **#18** lot weighing overwrites `Lot.total_weight` with a partial-sample weight
- `🟡 ◔` **#22** `register_placement` never bounds `head_count` against lot size or occupancy
- `🟡 ◔~` **#36** `register_calving` on a lot doesn't update counters, unlike Death/Exit
- `⚪ ○` **#29** `register_death`/`register_exit` skip the retroactive-date guard `register_weighing` enforces
- `⚪ ○~` **#32** `_reduce_lot` leaves counters inconsistent when `weight` is omitted

## 🔒 Concurrency — nothing takes a row lock — 3

Three domains, three analysts, one bug class. Every denormalized cache and derived counter is unguarded.

- `🟠 ◑~` **#5** `balance_cached` read-modify-write loses updates
- `🟠 ◑~` **#21** semen/embryo stock check-then-act allows oversell
- `🟡 ◔~` **#23** calf ear-tag count-then-create races

## 🚪 Harness gates with blind spots — 2

Broken gate, and the thing it guards is nonetheless still clean. Fix while that's true.

- `🟠 ◔` **#35** `check_api.py` never inspects `api_urls.py` — undeclared routes bypass the API.md gate
- `🟡 ○` **#39** `dispatch_guardians.py` watchlist has the identical blind spot

## 📄 ADR frontmatter validity — 3

Extends open upstream issue `jereezquerro92/alvs-feedlot-campo#66`, which had spotted only two of these.

- `🟠 ○` **#41** four ADRs carry invalid `status: proposed`
- `🟠 ○` **#43** adr-29 and adr-31 have no frontmatter block at all
- `⚪ ○~` **#45** adr-30's frontmatter says `active`, its body says `propuesto`

## 🖥️ Frontend correctness & a11y — 6

- `🟠 ◑` **#24** every SSR fetch has no timeout/AbortController — a backend stall hangs the request thread
- `🟠 ◔` **#7** expandable table row is mouse-only `<tr onclick>`, no keyboard path
- `🟡 ◔` **#11** hardcoded Spanish literals bypass the i18n catalog
- `⚪ ○~` **#17** required props with no fallback break adr-22 rule 1 zero-prop mount
- `⚪ ○` **#28** `pending` prop on the clients roster is dead code
- `⚪ ○~` **#31** no per-endpoint Cache-Control convention for m365 sub-fetches

## 🤖 Inference tiers — 3

- `🟠 ◑` **#13** duplicated consecutive user turn breaks Bedrock `converse` role alternation on *every* message
- `🟡 ◔~` **#25** Bedrock clients swallow failures into an empty string, persisting a blank audited answer
- `⚪ ○` **#19** dead async entrypoints wired to no view

## 🧯 Error handling & resilience — 4

- `🟠 ◔` **#6** `ingest_prices` only isolates `ConnectorError` — a raw network error kills the whole run
- `🟡 ◑~` **#30** a sender exception rolls back the whole `send_notification` txn, destroying the audit trail
- `🟡 ○` **#12** `ClientViewSet.account`/`outstanding` throw HTTP 500 instead of a clean 404
- `⚪ ○` **#14** `recompute_balance` is dead code — the repair for #5 exists but has no entrypoint

## 🌾 Domain gaps / unbuilt features — 3

- `🟠 ◑` **#9** the adr-25 rule 5 client-stock shortfall split was never implemented — client-stock feeding is charged nothing and unbounded
- `⚪ ○~` **#38** no `(site, date)` uniqueness on `WeatherLog`
- `⚪ ◑?` **#37** sanitary sequential attribution can mis-attribute an application

## 🐌 Query performance — 3

- `🟡 ◔` **#10** `mortality()` loads every `Death` row and filters in Python
- `🟡 ◔` **#26** `plan_schedule_for_client` is N+1 per enrollment×product
- `⚪ ◔` **#34** `pen_cost_summary` re-queries per pen row and sums in Python

## 🐳 Infra pinning & fail-closed — 5

- `🟡 ◔` **#40** backend Dockerfile floats the Python patch version off the REQUIREMENTS pin
- `⚪ ◔~` **#47** `deploy-prod.yml` preflight silently defaults `AWS_REGION` instead of failing closed
- `⚪ ○` **#42** CI/deploy Postgres floats to `postgres:17` vs the `17.9-bookworm` pin
- `⚪ ○~` **#46** frontend `/healthz` is a stub that can never fail — health gating proves nothing
- `⚪ ◑?` **#44** dev bind mount runs as uid 10001 over a host-owned tree

---

## Reading the board

Nothing is `● high` or `⬤ epic` effort. The worst is `◑ medium`; 20 of 47 are `○ trivial`.
There is no rewrite hiding in here — it is all bounded, local work.

**Cheapest high-value PR:** #1, #3, #27 are three `🔴🔴🟠` findings that close with one
shared positivity guard. Add #2 (one missing `no_feed_recorded` branch, copied from the
function that already has it) and #4, and four of five criticals clear in about a day.

The `~` and `?` markers deserve respect before anyone writes code: the concurrency trio
(#5, #21, #23) was reasoned about, not reproduced.

## Open thread

`origin` still points at `jereezquerro92/alvs-feedlot-campo` in both checkouts, and
`adr-08` rules 1/10 plus `docs/GH.md` still name the old owner. The fork exists and holds
the issues; the ownership migration was deliberately deferred to its own issue + PR batch
past the ADR guardian.
