# 10 · Estado — Fase 1 implementada

**Fecha:** 2026-07-21. **Rama:** `feat/feedlot-phase1` (sobre `main` del template).

La Fase 1 (núcleo operativo) está codificada y con tests pasando. Se entregó como paquete (`.zip` + `.patch`) para revisar y commitear por el flujo del repo.

## Apps creadas (backend Django)

- **`apps/clients`** — `Client` (hotelería/propio) + `Account` (se crea sola al crear el cliente). Saldo derivado del ledger; `balance_cached` es cache de lectura.
- **`apps/ledger`** — libro inmutable `LedgerEntry` + `Payment`. Servicios `post_entry`, `register_payment`, `recompute_balance`. Saldo positivo = el cliente debe. Correcciones por contra-asiento.
- **`apps/livestock`** — `Animal`, `Lot`, `Intake` (individual y por lote). Caravana única por cliente entre activos.
- **`apps/feed`** — `FeedType`, `FeedDelivery`, `FeedStockMovement`, `FeedingEvent`. **La regla de costeo** (`services.register_feeding`): alimento propio → salida de stock + **débito**; alimento del cliente → salida de stock, **sin cargo**. Stock = suma de movimientos.

Incluye migraciones, admin, viewsets/serializers DRF y el cableado en `config/settings.py` y `config/urls.py`.

## Endpoints (`/api/`)

`clients/`, `clients/{id}/account/`, `clients/{id}/ledger/`, `ledger-entries/`, `payments/`, `animals/`, `lots/`, `intakes/`, `feed-types/`, `feed-deliveries/`, `feedings/`, `feed-stock/`.

## Verificación

11 tests: regla de costeo (propio vs cliente), balance del ledger, pagos, contra-asientos, ingreso individual/lote, caravana única, target animal-xor-lote. Verificados con Django 5.2 sobre sqlite (el contenedor tenía Python 3.11; el repo usa Django 6). Migraciones aplican y `django check` limpio.

## Pendiente de integración por el harness

Son propuestas, a integrar por el ABC gate + guardians (no ediciones directas a las SSOT): filas para `GLOSSARY.md` y `API.md`, y los ADR 24–27 (confirmar numeración; el máximo actual del repo es adr-23). Colisión de nombre a resolver: el template ya tiene un app `health` (liveness `/api/health/`); la app de sanidad animal (Fase 2) debe renombrarse (p. ej. `sanitary`).

## Próximo (Fase 2)

Ciclo del animal: pesajes y crecimiento (GDP), muertes y salidas, y sanidad. Después: dashboard (Fase 3), precios de hacienda (Fase 4), asesores (Fase 5), y la app `services` para costos manuales (mano de obra, maquinaria, combustible) sin prorrateo.
