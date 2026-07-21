# API — feedlot additions (rows to merge into docs/API.md)

Per [[adr-03-api-and-backend]] an endpoint is valid **iff** it is a row in [[API]];
these enter that table before any `models.py`. All paths are under `/api/`, English,
trailing slash ([[LOCALIZATION]]); names follow [[GLOSSARY]] (`GLOSSARY-feedlot-additions.md`).
Auth is `session` (browser HTMX/JSON) unless noted. RBAC groups gating these are TBD in
[[adr-10-auth]] terms (e.g. a `feedlot_operators` Django group) — decide with the auth guardian.

Proposed rows (Phase 1–2 core; refine per endpoint as TDD entries are written):

| Method | Path | View/ViewSet | Serializer | Auth | Description |
|---|---|---|---|---|---|
| GET/POST | `/api/clients/` | `ClientViewSet` | `ClientSerializer` | session | List / create clients (`boarding` or `own`). |
| GET/PATCH | `/api/clients/{id}/` | `ClientViewSet` | `ClientSerializer` | session | Retrieve / update a client. |
| GET | `/api/clients/{id}/account/` | `AccountView` | `AccountSerializer` | session | Client account: cached balance + summary. |
| GET | `/api/clients/{id}/ledger/` | `LedgerEntryViewSet` | `LedgerEntrySerializer` | session | Movements for the client's account (read-only list, paginated, date-filtered). |
| POST | `/api/payments/` | `PaymentViewSet` | `PaymentSerializer` | session | Register a payment → emits a `credit` `LedgerEntry`. |
| POST | `/api/ledger/adjustments/` | `AdjustmentView` | `AdjustmentSerializer` | session | Post a manual adjustment / counter-entry (never edit an existing entry). |
| GET/POST | `/api/animals/` | `AnimalViewSet` | `AnimalSerializer` | session | List / create individual animals. |
| GET/PATCH | `/api/animals/{id}/` | `AnimalViewSet` | `AnimalSerializer` | session | Retrieve / update an animal (status transitions via events, not free edits). |
| GET/POST | `/api/lots/` | `LotViewSet` | `LotSerializer` | session | List / create lots (`anonymous` or `named`). |
| GET | `/api/lots/{id}/` | `LotViewSet` | `LotSerializer` | session | Lot detail: head count, total weight, derived averages. |
| POST | `/api/intakes/` | `IntakeViewSet` | `IntakeSerializer` | session | Cattle entry, `mode` = `individual` (creates `Animal`s) or `lot` (creates/updates a `Lot`). Contract below. |
| POST | `/api/weighings/` | `WeighingViewSet` | `WeighingSerializer` | session | Record a weight for an `animal` **or** `lot` (exactly one). |
| POST | `/api/deaths/` | `DeathViewSet` | `DeathSerializer` | session | Mortality for an animal or a partial lot. |
| POST | `/api/exits/` | `ExitViewSet` | `ExitSerializer` | session | Sale/removal for an animal or a partial lot. |
| GET/POST | `/api/feed-types/` | `FeedTypeViewSet` | `FeedTypeSerializer` | session | Feed catalog. |
| POST | `/api/feed-deliveries/` | `FeedDeliveryViewSet` | `FeedDeliverySerializer` | session | Client-provided feed → `in` stock movement to the client's stock. |
| GET | `/api/feed-stock/` | `FeedStockView` | `FeedStockSerializer` | session | Derived stock balances by (`owner_kind`, client, feed type). |
| GET | `/api/animals/{id}/growth/` | `AnimalViewSet.growth` | — | session | Weighing series + ADG between consecutive readings. |
| GET | `/api/lots/{id}/growth/` | `LotViewSet.growth` | — | session | Idem on weight **per head**; `adg=null` + `not_calculable` when the head count changed (adr-28). |
| GET/POST | `/api/health-products/` | `HealthProductViewSet` | `HealthProductSerializer` | session | Health catalogue (vaccines, treatments). Editable; price changes never rewrite past applications. |
| GET/POST | `/api/health-events/` | `HealthEventViewSet` | `HealthEventSerializer` | session | Record an application on an animal or lot. **Always** emits a `debit` `LedgerEntry` (`concept=health`). |
| POST | `/api/feedings/` | `FeedingEventViewSet` | `FeedingEventSerializer` | session | Record a ration: feed type, kg, `unit_price`, `origin`. Emits an `out` stock movement and, when `origin=own_stock`, a `debit` `LedgerEntry`. Contract below. |
| GET/POST | `/api/health-products/` | `HealthProductViewSet` | `HealthProductSerializer` | session | Vaccine/treatment catalog. |
| POST | `/api/health-events/` | `HealthEventViewSet` | `HealthEventSerializer` | session | Apply a vaccine/treatment → `debit` `LedgerEntry`. |
| GET | `/api/clients/{id}/dashboard/` | `ClientDashboardView` | — | session | Aggregated metrics for the client dashboard (Phase 3). JSON of derived series/cards. |
| GET/POST | `/api/market-prices/` | `MarketPriceViewSet` | `MarketPriceSerializer` | session | Reference cattle prices; POST for manual entry (Phase 4). |
| POST | `/api/advisors/{slug}/reports/` | `AdvisorReportView` | `AdvisorReportSerializer` | session; generative-gated | Generate an advisor report for a client+period (Phase 5). Read-only over data, per-client. Async ([[adr-16-async-mandatory]]). See [[adr-27-advisors-generative]]. |
| GET | `/api/clients/{id}/reports/` | `AdvisorReportViewSet` | `AdvisorReportSerializer` | session | Past advisor reports for a client. |

## Contracts (sketch — expand per endpoint in [[API]])

### POST `/api/intakes/`
Body carries `client`, `date`, `mode`. For `individual`: a list of `{ear_tag, category, sex, entry_weight}`. For `lot`: `{code, head_count, total_weight}`. Response returns created `Animal` ids or the `Lot` id.

### POST `/api/feedings/`
Body: `client`, target (`animal` **xor** `lot`), `feed_type`, `quantity`, `unit_price`, `origin`. Server validates stock for `origin=client_stock`; on shortfall applies the policy fixed by [[adr-25-account-ledger]] (default: serve available from client stock, remainder from own stock as a charged split — confirm). Emits the stock movement(s) and, for own-stock quantity, the `debit` entry.
