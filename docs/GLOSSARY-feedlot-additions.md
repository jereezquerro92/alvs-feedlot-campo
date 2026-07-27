# GLOSSARY — feedlot additions (rows to merge into docs/GLOSSARY.md)

Per [[adr-01-glossary-and-localization]] a term is decided here before its first use.
Merge these rows into the table in [[GLOSSARY]]; the format is
`Term | Canonical form | Applies to | Forbidden forms`.

| Term | Canonical form | Applies to | Forbidden forms |
|---|---|---|---|
| Django app (clients) | `clients` | client/account domain app ([[FEEDLOT]]) | `customers`, `accounts` (that is a model, not the app) |
| Django app (livestock) | `livestock` | cattle domain app ([[FEEDLOT]]) | `cattle`, `animals`, `cows` |
| Django app (feed) | `feed` | feed catalog/stock/rations app ([[FEEDLOT]]) | `feeding`, `food`, `nutrition` |
| Django app (health) | `health` | animal-health app ([[FEEDLOT]]); distinct from the `/api/health/` liveness path, which is owned by the `health` **liveness** app already in the template — resolve the collision before code (rename this app `sanitary` if needed) | `sanidad`, `vet` |
| Django app (ledger) | `ledger` | current-account app ([[adr-25-account-ledger]]) | `billing`, `accounting`, `cta` |
| Django app (market) | `market` | reference cattle-price app ([[FEEDLOT]]) | `prices`, `hacienda` |
| Django app (advisors) | `advisors` | AI-advisor app ([[adr-27-advisors-generative]]) | `advisor` (singular), `consultants` |
| model (client) | `Client` | boarding or own cattle owner ([[FEEDLOT-DATA-MODEL]]) | `Customer`, `Owner` |
| model field (client kind) | `kind` — `boarding` \| `own` | client type ([[FEEDLOT-DATA-MODEL]]) | `type`, `is_boarding`, Spanish values |
| model (account) | `Account` | a client's current account ([[adr-25-account-ledger]]) | `CurrentAccount`, `Wallet`, `Balance` |
| model (animal) | `Animal` | one head, ear-tagged ([[adr-26-livestock-individual-and-lot]]) | `Cow`, `Head`, `Cattle` |
| model field (ear tag) | `ear_tag` | animal identifier ([[FEEDLOT-DATA-MODEL]]) | `caravana`, `tag`, `rfid`, `earring` |
| model (lot) | `Lot` | a batch tracked by head + weight ([[adr-26-livestock-individual-and-lot]]) | `Batch`, `Group`, `Lote` |
| model field (lot mode) | `mode` — `anonymous` \| `named` | lot identity mode ([[adr-26-livestock-individual-and-lot]]) | `type`, `is_named` |
| model (intake) | `Intake` | cattle entry event ([[adr-26-livestock-individual-and-lot]]) | `Entry`, `Ingreso`, `Admission` |
| model field (intake mode) | `mode` — `individual` \| `lot` | intake mode ([[adr-26-livestock-individual-and-lot]]) | `type`, `by_lot` |
| model (weighing) | `Weighing` | weight record for an animal or lot ([[FEEDLOT-DATA-MODEL]]) | `Weight`, `Pesaje`, `Scale` |
| model (death) | `Death` | mortality event ([[FEEDLOT-DATA-MODEL]]) | `Mortality`, `Baja`, `Cull` |
| model (exit) | `Exit` | sale/removal event ([[FEEDLOT-DATA-MODEL]]) | `Sale`, `Egreso`, `Departure` |
| model (feed type) | `FeedType` | feed catalog item ([[FEEDLOT-DATA-MODEL]]) | `Feed`, `Food`, `Ration` |
| model (feed delivery) | `FeedDelivery` | client-provided feed intake ([[FEEDLOT-DATA-MODEL]]) | `Delivery`, `Supply` |
| model (feed stock movement) | `FeedStockMovement` | append-only stock in/out ([[FEEDLOT-DATA-MODEL]]) | `Stock`, `Inventory`, `StockLevel` |
| model field (stock owner) | `owner_kind` — `own` \| `client` | stock titularity ([[FEEDLOT-DATA-MODEL]]) | `owner`, `is_own` |
| model (feeding event) | `FeedingEvent` | a daily ration served ([[adr-25-account-ledger]]) | `Feeding`, `Ration`, `Meal` |
| model field (feed origin) | `origin` — `client_stock` \| `own_stock` | ration feed source ([[adr-25-account-ledger]]) | `source`, `from_client` |
| model (health product) | `HealthProduct` | vaccine/treatment catalog item ([[FEEDLOT-DATA-MODEL]]) | `Product`, `Vaccine`, `Drug` |
| model (health event) | `HealthEvent` | vaccine/treatment application ([[FEEDLOT-DATA-MODEL]]) | `Vaccination`, `Treatment`, `Sanidad` |
| model (ledger entry) | `LedgerEntry` | one immutable account movement ([[adr-25-account-ledger]]) | `Movement`, `Transaction`, `Entry` |
| model field (direction) | `direction` — `debit` \| `credit` | ledger sign ([[adr-25-account-ledger]]) | `type`, `sign`, `is_debit` |
| model field (concept) | `concept` — `feeding`\|`health`\|`service`\|`adjustment`\|`payment` | ledger entry category ([[adr-25-account-ledger]]) | `category`, `kind` |
| model field (origin ref) | `source_kind`, `source_id` | generic link from a `LedgerEntry`/`FeedStockMovement` to its originating event ([[adr-24-feedlot-domain]], [[adr-25-account-ledger]]) | a per-domain FK on `LedgerEntry`; `content_type`/`object_id` framing if a plain pair suffices |
| model (payment) | `Payment` | client money in ([[adr-25-account-ledger]]) | `Deposit`, `Pago`, `Receipt` |
| model (market source) | `MarketSource` | a cattle-price origin ([[FEEDLOT]]) | `Source`, `Market`, `Exchange` |
| model (market price) | `MarketPrice` | a reference price row ([[FEEDLOT]]) | `Price`, `Quote`, `Precio` |
| model (advisor) | `Advisor` | one of three AI-advisor roles ([[adr-27-advisors-generative]]) | `Consultant`, `Asesor` |
| model field (advisor slug) | `slug` — `livestock` \| `finance` \| `admin` | advisor role key ([[adr-27-advisors-generative]]) | `role`, `type`, Spanish values |
| model (advisor report) | `AdvisorReport` | a generated per-client analysis ([[adr-27-advisors-generative]]) | `Report`, `Analysis`, `Informe` |
| currency posture (account) | ARS, historical unit price snapshot per entry | `ledger` valuation ([[adr-25-account-ledger]]) | storing only a total without `unit_price`/`quantity`; recomputing past entries at today's price |
| Django app (assets) | `assets` | shared asset/task/maintenance abstractions app (Fase 6, [[adr-32-multi-rubro-assets]]) | `equipment`, `resources`, `activos` |
| Django app (crops) | `crops` | alfalfa/pivot crop domain app (Fase 6, [[adr-32-multi-rubro-assets]]) | `alfalfa`, `agriculture`, `fields`, `cultivos` |
| Django app (machinery) | `machinery` | machinery & maintenance domain app (Fase 6, [[adr-32-multi-rubro-assets]]) | `machines`, `equipment`, `maquinaria`, `taller` |
| model (asset base) | `AssetBase` (abstract) | shared lifecycle base for a `Pivot`/`Machine` ([[adr-32-multi-rubro-assets]]) | `Asset` (concrete), `Resource`, `Activo` |
| model (costed event base) | `CostedEvent` (abstract) | shared base for an event that snapshots `unit_price`×`quantity` and posts a `service` debit ([[adr-32-multi-rubro-assets]]) | `Chargeable`, `Billable`, `CostEvent` |
| model (pivot) | `Pivot` | a center-pivot irrigation circle (círculo) ([[adr-32-multi-rubro-assets]]) | `Circle`, `Circulo`, `IrrigationUnit`, `Field` |
| model (crop) | `Crop` | a planting standing on a `Pivot` ([[adr-32-multi-rubro-assets]]) | `Planting`, `Cultivo`, `Plantation` |
| model field (crop species) | `species` — `alfalfa` \| `other` | crop species ([[adr-32-multi-rubro-assets]]) | `type`, `kind`, `plant`, Spanish values |
| model (cutting) | `Cutting` | a harvest event on a crop (corte); posts NO ledger entry ([[adr-32-multi-rubro-assets]]) | `Harvest`, `Corte`, `Mowing`, `Cut` |
| model (field task) | `FieldTask` | labor on a `Pivot` (tarea); posts a `service` debit ([[adr-32-multi-rubro-assets]]) | `Task` (bare — collides), `Labor`, `Tarea`, `WorkOrder` |
| model field (field task category) | `category` — `sowing`\|`fertilizing`\|`irrigation`\|`weeding`\|`other` | field-task category ([[adr-32-multi-rubro-assets]]) | `type`, `kind`, Spanish values |
| model (machine) | `Machine` | a piece of machinery (maquinaria) ([[adr-32-multi-rubro-assets]]) | `Equipment`, `Maquina`, `Vehicle`, `Tractor` |
| model field (machine category) | `category` — `tractor`\|`harvester`\|`mixer`\|`truck`\|`other` | machine category ([[adr-32-multi-rubro-assets]]) | `type`, `kind`, Spanish values |
| model (maintenance event) | `MaintenanceEvent` | a service/repair on a `Machine` (mantenimiento); posts a `service` debit ([[adr-32-multi-rubro-assets]]) | `Maintenance`, `Service`, `Repair`, `Mantenimiento` |
| model field (maintenance kind) | `kind` — `preventive`\|`corrective`\|`other` | maintenance-event kind ([[adr-32-multi-rubro-assets]]) | `type`, `category`, Spanish values |
| ledger origin ref values (Fase 6) | `source_kind` ∈ `field_task`, `maintenance_event` | generic `LedgerEntry` back-links for the two charge-bearing Fase 6 events ([[adr-32-multi-rubro-assets]], [[adr-25-account-ledger]]) | a per-domain FK; new `Concept` values (both reuse `service`) |
| Django app (feedyard) | `feedyard` | pen/ration/loading/bunk operating-loop app (Fase 7, [[adr-33-feedyard-operating-loop]]) | `pens`, `corral`, `corrales`, `bunk`, `feeding` (that is the `feed` app) |
| model (pen) | `Pen` | a physical feedlot pen — corral (Fase 7, [[adr-33-feedyard-operating-loop]]) | `Corral`, `Yard`, `Paddock`, `Lot` (that is a cattle batch) |
| model field (pen status) | `status` — `active` \| `inactive` | pen availability ([[adr-33-feedyard-operating-loop]]) | `is_active`, `retired`, Spanish values |
| model (ration) | `Ration` | a named diet/recipe — dieta (Fase 7, [[adr-33-feedyard-operating-loop]]) | `Diet`, `Recipe`, `Dieta`, `Formula`, `FeedType` (catalog item, not a recipe) |
| model (ration line) | `RationLine` | one `FeedType` share within a `Ration` ([[adr-33-feedyard-operating-loop]]) | `DietLine`, `Ingredient`, `Component`, `RationItem` |
| model field (ration line share) | `proportion` (percent), `dry_matter_pct` | ration composition on an as-fed / dry-matter basis ([[adr-33-feedyard-operating-loop]]) | `pct`, `ratio`, `dm`, `percentage`, Spanish values |
| model (loading order) | `LoadingOrder` | the **planned** mixer load for a pen+ration on a date — orden de carga; posts NO ledger entry (Fase 7, [[adr-33-feedyard-operating-loop]]) | `Load`, `MixOrder`, `OrdenDeCarga`, `Delivery`, `FeedingEvent` (that is the executed ration) |
| model field (loading order planned) | `planned_as_fed_kg` | planned as-fed kilograms to deliver ([[adr-33-feedyard-operating-loop]]) | `kg`, `amount`, `quantity` alone (ambiguous as-fed vs dry-matter) |
| model (bunk score) | `BunkScore` | a daily bunk (feed-trough) reading per pen — lectura de comedero; posts NO ledger entry (Fase 7, [[adr-33-feedyard-operating-loop]]) | `Reading`, `Comedero`, `TroughScore`, `FeedScore` |
| model field (bunk score value) | `score` — `0`\|`1`\|`2`\|`3`\|`4` | standard 0–4 bunk score ([[adr-33-feedyard-operating-loop]]) | `rating`, `level`, `grade` |
| model field (feeding pen link) | `pen` (nullable FK on `FeedingEvent`) | the pen a served ration belongs to — additive, backward-compatible (Fase 7, [[adr-33-feedyard-operating-loop]]) | making it required; a second parallel feeding table per pen |
| model (pen placement) | `PenPlacement` | an immutable event that moves an `Animal` or `Lot` into or out of a `Pen` — ubicación en corral (Fase 7b, [[adr-34-pen-placement]]) | `Placement`, `PenAssignment`, `Location`, `Move`, `Ubicacion` |
| model field (placement direction) | `direction` — `in` \| `out` | whether cattle enter or leave the pen ([[adr-34-pen-placement]]) | `way`, `type`, `entry`/`exit` as values, Spanish values |
| model field (placement head count) | `head_count` (nullable) | head moved for a partial lot placement; `null`/`1` for an individual animal ([[adr-34-pen-placement]]) | `heads`, `qty`, `count` |
| derived metric (pen occupancy) | `pen_occupancy` | current head in a pen = Σ head(in) − Σ head(out); never a stored number ([[adr-34-pen-placement]]) | `occupancy` as a stored field, `Pen.head_count` |
| Django app (assistant) | `assistant` | conversational read-only generating tier — asistente (Fase 8, [[adr-35-conversational-assistant]]) | `chatbot` (that is the `router` app), `chat`, `copilot`, `asistente`, `bot` |
| model (conversation) | `Conversation` | a per-client Q&A thread — conversación (Fase 8, [[adr-35-conversational-assistant]]) | `Thread`, `Chat`, `Session`, `Conversacion` |
| model (message) | `Message` | one turn in a conversation (Fase 8, [[adr-35-conversational-assistant]]) | `Turn`, `Utterance`, `Mensaje`, `ChatMessage` |
| model field (message role) | `role` — `user` \| `assistant` | who authored the turn ([[adr-35-conversational-assistant]]) | `sender`, `author`, `from`, Spanish values |
| Django app (notifications) | `notifications` | outbound weekly-digest + delivery-record app (Fase 9, [[adr-36-notifications-digest]]) | `notify`, `alerts`, `messaging`, `notificaciones`, `push` |
| model (notification) | `Notification` | an immutable record of one send attempt — notificación (Fase 9, [[adr-36-notifications-digest]]) | `Message` (that is an assistant turn), `Alert`, `Notificacion`, `Digest` |
| model field (notification channel) | `channel` — `whatsapp` \| `email` | the delivery channel of a notification ([[adr-36-notifications-digest]]) | `medium`, `via`, `transport`, Spanish values |
| model field (notification status) | `status` — `pending` \| `sent` \| `failed` | the outcome of a send attempt ([[adr-36-notifications-digest]]) | `state`, `delivered`, `ok`/`error` as values, Spanish values |
| Django app (inventory) | `inventory` | general (non-feed) input stock app — gasoil/postes/alambre/sanitario (Fase 10, [[adr-37-inventory-and-weather]]) | `stock` (that is a derived quantity, not an app), `supplies`, `inputs`, `inventario`, `warehouse` |
| model (input type) | `InputType` | a general input catalog item — tipo de insumo (Fase 10, [[adr-37-inventory-and-weather]]) | `Supply`, `Item`, `Material`, `Insumo`, `FeedType` (that is feed only) |
| model (input stock movement) | `InputStockMovement` | an immutable in/out movement of an `InputType`; stock is Σin−Σout, never stored (Fase 10, [[adr-37-inventory-and-weather]]) | `StockEntry`, `Movement`, `Movimiento`, `FeedStockMovement` (that is feed only) |
| model field (input movement direction) | `direction` — `in` \| `out` | whether the input enters or leaves stock ([[adr-37-inventory-and-weather]]) | `type`, `way`, `entry`/`exit` as values, Spanish values |
| derived metric (input stock) | `input_stock` | current stock of an input = Σ quantity(in) − Σ quantity(out); never a stored field ([[adr-37-inventory-and-weather]]) | `stock` as a stored field, `InputType.quantity` |
| Django app (weather) | `weather` | rainfall/weather log app — registro de clima (Fase 10, [[adr-37-inventory-and-weather]]) | `climate`, `rain`, `clima`, `meteo` |
| model (weather log) | `WeatherLog` | an immutable per-date weather record — registro de clima (Fase 10, [[adr-37-inventory-and-weather]]) | `Weather`, `RainLog`, `Climate`, `RegistroClima` |
| model field (rainfall) | `rainfall_mm` | millimetres of rain logged for a date ([[adr-37-inventory-and-weather]]) | `rain`, `mm`, `precipitation`, `lluvia`, Spanish values |
| Django app (traceability) | `traceability` | SENASA traceability app — RENSPA/DT-e/caravana (Fase 11, [[adr-38-senasa-traceability]]) | `senasa`, `renspa` (that is a field), `dte`, `tracing`, `trazabilidad` |
| model (establishment) | `Establishment` | an editable RENSPA-registered establishment — establecimiento (Fase 11, [[adr-38-senasa-traceability]]) | `Farm`, `Site`, `Renspa`, `Establecimiento`, `Ranch` |
| model field (renspa) | `renspa` | the SENASA RENSPA registry number of an `Establishment` ([[adr-38-senasa-traceability]]) | `registry`, `code`, `senasa_id`, Spanish values |
| model (transit document) | `TransitDocument` | an immutable DT-e linking an origin RENSPA to a destination RENSPA — documento de tránsito (Fase 11, [[adr-38-senasa-traceability]]) | `DTe`, `Transit`, `Movement`, `Guia`, `TransitoDocumento` |
| model field (dte number) | `dte_number` | the official DT-e number of a `TransitDocument` ([[adr-38-senasa-traceability]]) | `number`, `dte`, `document_number`, Spanish values |
| model (caravana) | `Caravana` | the official individual ear-caravan identifier linked to an `Animal` — caravana oficial (Fase 11, [[adr-38-senasa-traceability]]) | `Tag`, `EarTag` (that is the internal `ear_tag`), `Rfid`, `OfficialTag` |
| model field (official number) | `official_number` | the unique SENASA caravan number of a `Caravana` ([[adr-38-senasa-traceability]]) | `number`, `caravana`, `tag_number`, Spanish values |
| derived metric (caravana coverage) | `caravana_coverage` | share of a client's active head that carry an official caravana; `null` when there is no active head ([[adr-38-senasa-traceability]], [[adr-29-metrics-derivation]]) | `coverage` as a stored field, a filled `0` when there is no head |
| Django app (fx) | `fx` | reference exchange-rate series app — tipo de cambio (Fase 12, [[adr-39-gross-margin-and-fx]]) | `forex`, `currency`, `exchange`, `cambio`, `tc` |
| model (fx rate) | `FxRate` | an idempotent reference exchange rate per `(currency, date, source)`; ARS per one unit of `currency` — never redenominates the ledger (Fase 12, [[adr-39-gross-margin-and-fx]]) | `Exchange`, `Rate`, `Currency`, `TipoCambio`, `Dolar` |
| model field (fx currency) | `currency` | the non-ARS currency code priced by an `FxRate`, e.g. `USD` ([[adr-39-gross-margin-and-fx]]) | `code`, `moneda`, `divisa` |
| model field (fx rate value) | `rate` | ARS per one unit of `currency` on a date ([[adr-39-gross-margin-and-fx]]) | `value`, `price`, `cotizacion`, `valor` |
| derived metric (gross margin) | `gross_margin` | reference income (kg produced × market price) − period cost (debits); `null`+motivo when any input is missing; optionally expressed via `FxRate` ([[adr-39-gross-margin-and-fx]], [[adr-29-metrics-derivation]]) | `margin` as a stored field, `profit`, `margen`, a filled `0` on missing input |
| model (sanitary plan) | `SanitaryPlan` | a reusable editable template of scheduled sanitary applications — plan sanitario (Fase 13, [[adr-40-sanitary-plan-schedule]]) | `VaccinationPlan`, `HealthPlan`, `Calendar`, `PlanSanitario`, `Schedule` |
| model (sanitary plan item) | `SanitaryPlanItem` | one scheduled dose within a `SanitaryPlan`: a `HealthProduct` at a relative `day_offset` ([[adr-40-sanitary-plan-schedule]]) | `PlanLine`, `ScheduleItem`, `Dose`, `PlanItem`, `Item` |
| model field (plan item offset) | `day_offset` | days after a `PlanEnrollment.start_date` at which the dose is due ([[adr-40-sanitary-plan-schedule]]) | `offset`, `day`, `days`, `when`, Spanish values |
| model (plan enrollment) | `PlanEnrollment` | an immutable event binding a `SanitaryPlan` to one `Animal` XOR `Lot` with a `start_date` — inscripción; posts NO ledger entry ([[adr-40-sanitary-plan-schedule]]) | `Enrollment`, `PlanAssignment`, `Subscription`, `Inscripcion` |
| derived status (plan dose) | `applied` \| `pending` \| `upcoming` | a scheduled dose's derived state: applied when a matching `HealthEvent` exists, else pending if due, else upcoming; never stored ([[adr-40-sanitary-plan-schedule]]) | a stored `status` field on the item, a `done` boolean, Spanish values |
| model (payment allocation) | `PaymentAllocation` | an immutable link from a `Payment` to a debit `LedgerEntry` with an `amount`; imputes a payment to a charge and posts NO ledger entry, moves NO balance (Fase 4a, [[adr-41-payment-allocation]]) | `Imputation`, `Settlement`, `Allocation` as a stored balance, `Imputacion`, mutating the entry |
| derived metric (outstanding charges) | `outstanding_charges` | per debit: `amount`, `allocated` (Σ `PaymentAllocation.amount`), `outstanding` (`amount`−allocated); never a stored field ([[adr-41-payment-allocation]]) | a stored `paid`/`outstanding` field on `LedgerEntry`, Spanish keys |
| default imputation policy | `fifo` | auto-imputation applies a payment to the oldest unpaid debit first ([[adr-41-payment-allocation]]) | `lifo`, `proportional`, a per-caller ad-hoc policy, Spanish values |
| RBAC group (field manager) | `field_managers` | encargado del campo — sees all operational data, writes charges/payments ([[adr-44-field-operational-roles]]) | `field_manager` (singular), `managers`, `encargado`, `supervisor` |
| RBAC group (mixer operator) | `feed_operators` | operativo — prepares the mixer: loading orders, feedings, bunk scores ([[adr-44-field-operational-roles]]) | `feed_operator` (singular), `operators`, `mixer`, `operativo` |
| RBAC group (lot owner) | `lot_owners` | dueño de lote — client-portal, read-only, scoped to own `Client` ([[adr-44-field-operational-roles]]) | `lot_owner` (singular), `clients` (that is the app), `owners`, `dueños` |
| RBAC group (field admin) | `field_admins` | administrativo del campo — loads merchandise into stocks (own + client-contract) ([[adr-44-field-operational-roles]]) | `field_admin` (singular), `admins` (that is the superset group), `administrativo` |
| RBAC group (feedlot owner) | `feedlot_owners` | dueño del campo — reads across all clients (head per contract and own) ([[adr-44-field-operational-roles]]) | `feedlot_owner` (singular), `owner`, `dueño`, `boss` |
| RBAC group (workshop) | `workshop` | usuarios de taller — machinery, maintenance, fuel, crops/alfalfa ([[adr-44-field-operational-roles]]) | `workshops`, `taller`, `mechanics`, `machinery` (that is the app) |
| model field (user→client binding) | `client` (nullable FK on `AccessRequest`) | the single `Client` a `lot_owners` session is confined to; set by an admin, never self-service ([[adr-44-field-operational-roles]], [[adr-20-authorization-lobby]]) | `tenant`, `scope`, `owned_client`, putting the FK on `User` |
| permission class (client scope) | `ClientScopedReadPermission` | gates a `lot_owners` session to routes whose `client_id`/`pk` matches its bound `client`; read-only ([[adr-44-field-operational-roles]]) | `ClientScopedPermission` (drop the `Read`), `TenantPermission`, `OwnClientOnly`, scoping via queryset filtering across domain models |
| permission base (role matrix) | `GroupMatrixPermission` | base with `read_groups`/`write_groups` per functional area; `admins` always passes ([[adr-44-field-operational-roles]]) | `RolePermission`, a permission class per role×area combination |
