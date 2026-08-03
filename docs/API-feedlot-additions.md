---
title: API-feedlot-additions
type: reference
category: backend
use_case: merging the feedlot's endpoint rows into API
created: 2026-07-21
modified: 2026-08-02
tags: [doc, api, feedlot, ssot]
---

# API — feedlot additions (rows to merge into docs/API.md)

Per [[adr-51-api-and-backend]] an endpoint is valid **iff** it is a row in [[API]];
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
| GET | `/api/clients/{id}/metrics/summary/` | `SummaryView` | — | session | Dashboard header: herd, balance, cost, conversion, mortality, inconsistencies. `?start=&end=`. |
| GET | `/api/clients/{id}/metrics/daily-cost/` | `DailyCostView` | — | session | Daily charges broken down by concept. |
| GET | `/api/clients/{id}/metrics/growth/` | `GrowthView` | — | session | Kilos gained + how many segments were measured vs skipped. |
| GET | `/api/clients/{id}/metrics/conversion/` | `ConversionView` | — | session | Feed conversion. `null` + `not_calculable` when there is no honest divisor (adr-29). |
| GET | `/api/clients/{id}/metrics/mortality/` | `MortalityView` | — | session | Dead head / head entered in the period. |
| GET | `/api/clients/{id}/metrics/account/` | `AccountEvolutionView` | — | session | Running balance with opening and closing. |
| GET | `/api/advisors/` | `AdvisorViewSet` | `AdvisorSerializer` | session | Catálogo de asesores (livestock, finance, admin). Read-only. |
| GET | `/api/advisor-reports/` | `AdvisorReportViewSet` | `AdvisorReportSerializer` | session | Reportes generados. Filtra por `?client=&advisor=`. Leer no re-infiere. |
| POST | `/api/advisor-reports/` | `AdvisorReportViewSet` | `GenerateReportSerializer` | session | Genera un reporte para un cliente/período. Snapshot armado en backend, scope por cliente. |
| GET/POST | `/api/market-sources/` | `MarketSourceViewSet` | `MarketSourceSerializer` | session | Catálogo de fuentes de precios (canuelas, ipcva, rosgan, manual). |
| GET | `/api/market-prices/` | `MarketPriceViewSet` | `MarketPriceSerializer` | session | Precios de referencia. Filtra por `?source=&category=&date=`. |
| POST | `/api/market-prices/` | `MarketPriceViewSet` | `ManualPriceSerializer` | session | Carga manual de un precio (respaldo). Idempotente por (fuente, categoría, fecha). |
| GET/POST | `/api/health-products/` | `HealthProductViewSet` | `HealthProductSerializer` | session | Health catalogue (vaccines, treatments). Editable; price changes never rewrite past applications. |
| GET/POST | `/api/health-events/` | `HealthEventViewSet` | `HealthEventSerializer` | session | Record an application on an animal or lot. **Always** emits a `debit` `LedgerEntry` (`concept=health`). |
| POST | `/api/feedings/` | `FeedingEventViewSet` | `FeedingEventSerializer` | session | Record a ration: feed type, kg, `unit_price`, `origin`. Emits an `out` stock movement and, when `origin=own_stock`, a `debit` `LedgerEntry`. Contract below. |
| GET/POST | `/api/health-products/` | `HealthProductViewSet` | `HealthProductSerializer` | session | Vaccine/treatment catalog. |
| POST | `/api/health-events/` | `HealthEventViewSet` | `HealthEventSerializer` | session | Apply a vaccine/treatment → `debit` `LedgerEntry`. |
| GET | `/api/clients/{id}/dashboard/` | `ClientDashboardView` | — | session | Aggregated metrics for the client dashboard (Phase 3). JSON of derived series/cards. |
| GET/POST | `/api/market-prices/` | `MarketPriceViewSet` | `MarketPriceSerializer` | session | Reference cattle prices; POST for manual entry (Phase 4). |
| POST | `/api/advisors/{slug}/reports/` | `AdvisorReportView` | `AdvisorReportSerializer` | session; generative-gated | Generate an advisor report for a client+period (Phase 5). Read-only over data, per-client. Async ([[adr-16-async-mandatory]]). See [[adr-27-advisors-generative]]. |
| GET | `/api/clients/{id}/reports/` | `AdvisorReportViewSet` | `AdvisorReportSerializer` | session | Past advisor reports for a client. |

### breeding — Cría phase ([[adr-46-breeding-reproduction]])

RBAC: reproductive load is `field_managers` + `feed_operators` (write); reads follow each
role's rules ([[adr-44-field-operational-roles]] d7). `BreedingAccess` =
`GroupMatrixPermission` area in `apps/users/roles.py`
(`write_groups={field_managers, feed_operators}`,
`read_groups={field_managers, feed_operators, feedlot_owners}`).
Events are `list`/`retrieve`/`create` only — no `update`/`destroy` ([[adr-24-feedlot-domain]] r3).

| Method | Path | View/ViewSet | Serializer | Auth | Description |
|---|---|---|---|---|---|
| GET/POST | `/api/services/` | `ServiceViewSet` | `ServiceSerializer` | `BreedingAccess` | Register a service (`natural`/`ai`/`iatf`/`embryo_transfer`) on an `animal` **xor** `lot`. `register_service` decrements a `SemenMovement`/`EmbryoMovement` `out`; `ai`/`iatf` on a `boarding` client posts a `service` `debit` (`source_kind="breeding_service"`). Contract below. |
| GET | `/api/services/{id}/` | `ServiceViewSet` | `ServiceSerializer` | `BreedingAccess` | Retrieve a service (immutable). |
| GET/POST | `/api/pregnancy-checks/` | `PregnancyCheckViewSet` | `PregnancyCheckSerializer` | `BreedingAccess` | Record a `tacto`/ultrasound → `result` (`pregnant`/`empty`/`uncertain`). Posts no ledger entry. Estimated calving date is derived. |
| GET | `/api/pregnancy-checks/{id}/` | `PregnancyCheckViewSet` | `PregnancyCheckSerializer` | `BreedingAccess` | Retrieve a pregnancy check. |
| GET/POST | `/api/calvings/` | `CalvingViewSet` | `CalvingSerializer` | `BreedingAccess` | Record a `parición`; a `live` individual calving creates a `calf` `Animal` (`Calving.calf`). Genealogy is derived, no field added to `Animal`. Posts no ledger entry. Contract below. |
| GET | `/api/calvings/{id}/` | `CalvingViewSet` | `CalvingSerializer` | `BreedingAccess` | Retrieve a calving. |
| GET/POST | `/api/weanings/` | `WeaningViewSet` | `WeaningSerializer` | `BreedingAccess` | Record a `destete` with `weaning_weight` and `purpose` (`replacement`/`sale`/`undecided`). Posts no ledger entry. |
| GET | `/api/weanings/{id}/` | `WeaningViewSet` | `WeaningSerializer` | `BreedingAccess` | Retrieve a weaning. |
| GET/POST | `/api/iatf-protocols/` | `IatfProtocolViewSet` | `IatfProtocolSerializer` | `BreedingAccess` | IATF protocol template (name, steps). Editable catalog — full CRUD. |
| GET/PATCH/DELETE | `/api/iatf-protocols/{id}/` | `IatfProtocolViewSet` | `IatfProtocolSerializer` | `BreedingAccess` | Retrieve/update/deactivate a protocol; steps edited nested. `day_offset` is relative; absolute dates derived from `Service.date`. |
| GET | `/api/clients/{id}/metrics/reproduction/` | `ReproductionView` | — | `ClientScopedReadPermission` | Reproductive KPIs: `pregnancy_rate`, `calving_rate`, `weaning_rate`, `calving_interval`, `kg_weaned_per_dam`. Each `null` + `not_calculable` when the input is missing (adr-29). `?start=&end=`. |

### genetics — Cría phase ([[adr-47-genetics-semen-embryo]])

RBAC: genetic catalog, semen/embryo inventory and semen sales are `field_managers` (write);
reads follow role rules. `GeneticsAccess` = `GroupMatrixPermission` area in `apps/users/roles.py`.
Catalogs are full CRUD; movements/flushes/sales are `list`/`retrieve`/`create` only.

| Method | Path | View/ViewSet | Serializer | Auth | Description |
|---|---|---|---|---|---|
| GET/POST | `/api/sires/` | `SireViewSet` | `SireSerializer` | `GeneticsAccess` | Bull catalog: own (`animal` FK) or external (`registry_id`, `breed`). Editable — full CRUD. |
| GET/PATCH/DELETE | `/api/sires/{id}/` | `SireViewSet` | `SireSerializer` | `GeneticsAccess` | Retrieve/update/deactivate a sire. |
| GET/POST | `/api/breeding-values/` | `BreedingValueViewSet` | `BreedingValueSerializer` | `GeneticsAccess` | DEP/EPD rows (`trait`, `value`, `accuracy`, `source`, `date`). Editable catalog, loaded not derived (adr-47 d3). |
| GET/PATCH/DELETE | `/api/breeding-values/{id}/` | `BreedingValueViewSet` | `BreedingValueSerializer` | `GeneticsAccess` | Retrieve/update/delete a breeding value. |
| GET/POST | `/api/semen-batches/` | `SemenBatchViewSet` | `SemenBatchSerializer` | `GeneticsAccess` | Semen batch catalog (sire, tank/position, `unit_cost` informational). Straws remaining derived Σin−Σout. |
| GET/PATCH/DELETE | `/api/semen-batches/{id}/` | `SemenBatchViewSet` | `SemenBatchSerializer` | `GeneticsAccess` | Retrieve/update/deactivate a semen batch. |
| GET/POST | `/api/semen-movements/` | `SemenMovementViewSet` | `SemenMovementSerializer` | `GeneticsAccess` | Immutable `in`/`out` straw movement. `register_semen_movement` gates an inactive batch / non-positive qty. Posts no ledger entry. |
| GET | `/api/semen-movements/{id}/` | `SemenMovementViewSet` | `SemenMovementSerializer` | `GeneticsAccess` | Retrieve a semen movement. |
| GET/POST | `/api/semen-sales/` | `SemenSaleViewSet` | `SemenSaleSerializer` | `GeneticsAccess` | Register a semen sale → `register_semen_sale` posts a `sale` `credit` to the **own** account (`source_kind="semen_sale"`) + a `SemenMovement` `out` (`reason=sale`). Buyer informational. Contract below. |
| GET | `/api/semen-sales/{id}/` | `SemenSaleViewSet` | `SemenSaleSerializer` | `GeneticsAccess` | Retrieve a semen sale (immutable). |
| GET/POST | `/api/embryo-batches/` | `EmbryoBatchViewSet` | `EmbryoBatchSerializer` | `GeneticsAccess` | Embryo batch catalog (donor, sire, grade). Embryos remaining derived Σin−Σout. |
| GET/PATCH/DELETE | `/api/embryo-batches/{id}/` | `EmbryoBatchViewSet` | `EmbryoBatchSerializer` | `GeneticsAccess` | Retrieve/update/deactivate an embryo batch. |
| GET/POST | `/api/embryo-movements/` | `EmbryoMovementViewSet` | `EmbryoMovementSerializer` | `GeneticsAccess` | Immutable `in`/`out` embryo movement. Posts no ledger entry. |
| GET | `/api/embryo-movements/{id}/` | `EmbryoMovementViewSet` | `EmbryoMovementSerializer` | `GeneticsAccess` | Retrieve an embryo movement. |
| GET/POST | `/api/embryo-flushes/` | `EmbryoFlushViewSet` | `EmbryoFlushSerializer` | `GeneticsAccess` | Register a donor collection (`colecta`) → `register_embryo_flush` creates/updates an `EmbryoBatch` + posts an `EmbryoMovement` `in`. Posts no ledger entry. |
| GET | `/api/embryo-flushes/{id}/` | `EmbryoFlushViewSet` | `EmbryoFlushSerializer` | `GeneticsAccess` | Retrieve an embryo flush. |
| GET | `/api/semen-stock/` | `SemenStockView` | — | `GeneticsAccess` | Derived straw stock by batch and by sire, total available, use per sire. `null` + reason when no movements (adr-29). `?sire=&semen_batch=&start=&end=`. |

## Contracts (sketch — expand per endpoint in [[API]])

### POST `/api/intakes/`
Body carries `client`, `date`, `mode`. For `individual`: a list of `{ear_tag, category, sex, entry_weight}`. For `lot`: `{code, head_count, total_weight}`. Response returns created `Animal` ids or the `Lot` id.

### POST `/api/feedings/`
Body: `client`, target (`animal` **xor** `lot`), `feed_type`, `quantity`, `unit_price`, `origin`. Server validates stock for `origin=client_stock`; on shortfall applies the policy fixed by [[adr-25-account-ledger]] (default: serve available from client stock, remainder from own stock as a charged split — confirm). Emits the stock movement(s) and, for own-stock quantity, the `debit` entry.

### POST `/api/services/`
Body: target (`animal` **xor** `lot`), `date`, `method` (`natural`/`ai`/`iatf`/`embryo_transfer`), optional `sire`, `semen_batch` (for `ai`/`iatf`), `embryo_batch` (for `embryo_transfer`), `protocol` (for `iatf`), `service_price` (the insemination fee), `note`. `register_service` validates in the service layer ([[adr-46-breeding-reproduction]] d7): target active and belonging to the client, exact `animal`/`lot` XOR, batch active with stock, protocol active. It decrements one `SemenMovement`/`EmbryoMovement` `out`; and only for `method ∈ {ai, iatf}` on a `Client(kind=boarding)` target posts a `service` `debit` via `(source_kind="breeding_service", source_id)` snapshotting `service_price` (d6). Natural / own-cattle services post no ledger entry.

### POST `/api/calvings/`
Body: target (`animal` **xor** `lot`), `date`, `outcome` (`live`/`stillborn`/`aborted`), `calving_ease`, optional `calf_sex`, `calf_weight`, `births_count` (lot), `service`, `note`. A `live` **individual** calving creates a `calf` `Animal` (`category=calf`, `client` = the dam's client) and links it as `Calving.calf`; a `lot` calving adds `births_count` head to the calf lot without per-head identity ([[adr-26-livestock-individual-and-lot]] r1). Genealogy (dam = target, sire = `service.sire`) is **derived** — no `dam`/`sire` field is added to `Animal` (adr-46 d4). Posts no ledger entry.

### POST `/api/semen-sales/`
Body: `semen_batch`, `date`, `straws`, `unit_price` (ARS/straw), `buyer_name`, optional `buyer_client`, `note`. `register_semen_sale` rejects insufficient stock and a non-positive price, then in one transaction posts a `sale` **`credit`** to the **own** account (`Client(kind=own)`) via `(source_kind="semen_sale", source_id)` snapshotting `unit_price`×`straws` ([[adr-47-genetics-semen-embryo]] d4, [[adr-43-sale-settlement]] precedent) and a `SemenMovement` `out` (`reason=sale`). The buyer is informational — no charge is posted to a buyer in this cut.
