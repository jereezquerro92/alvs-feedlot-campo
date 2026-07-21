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
