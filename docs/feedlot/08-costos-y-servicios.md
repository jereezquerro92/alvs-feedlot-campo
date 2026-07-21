# 08 · Costos y servicios (más allá del alimento)

Además de la alimentación y la sanidad, hay costos que también deben cargarse a la cuenta corriente de cada cliente: **mano de obra, uso de maquinaria, combustible, fletes y servicios varios**. Este documento los incorpora al modelo con el mismo criterio que el resto: precio del momento, trazabilidad e inmutabilidad.

## La pieza: catálogo de servicios + cargos

Se agrega una app de dominio `services` (columna vertebral, reutilizable por otros rubros) con dos entidades:

**ServiceType** (catálogo, editable)
- `name` — descripción del servicio.
- `category` — `labor` (mano de obra) | `machinery` (uso de maquinaria) | `fuel` (combustible) | `freight` (flete) | `service` (servicio general) | `other`.
- `unit` — unidad de medida (hora, día, litro, km, unidad…).
- `unit_price` — precio de referencia (editable), que se copia al cargar.
- `is_active`.

**ServiceCharge** (evento inmutable)
- `client` — a quién se le cobra (FK).
- `date`.
- `service_type` — FK.
- `quantity` — cantidad (horas, litros, km…).
- `unit_price` — precio del momento (histórico).
- `total_cost` — derivado.
- `target` — opcional: lote o animal al que se imputa.
- `description`.
- Efecto: genera un `LedgerEntry` de **débito** con `concept = service`.

## Por qué encaja sin romper nada

`ServiceCharge` es exactamente el mismo patrón que `FeedingEvent` (con origen propio) y `HealthEvent`: un evento con costo que postea un débito a la cuenta usando el **seam genérico** del ledger (`source_kind = service_charge`, `source_id`). No hay que tocar el `ledger` ni el resto del sistema; es "crecer por adición" otra vez.

## Regla de asignación (DECIDIDO)

- **Carga manual y directa por cliente.** Cada costo se imputa a mano al cliente (y opcionalmente al lote/animal) que corresponde. **No hay prorrateo automático** de costos generales entre clientes. Si un gasto es de varios, el operador lo carga dividido como prefiera, pero el sistema no reparte solo.
- **Sin cálculo de rentabilidad.** El sistema registra y cobra costos; **no** calcula márgenes ni rentabilidad. Los precios de hacienda ([06](feedlot/06-precios-hacienda.md)) quedan solo como referencia informativa, no para estimar ganancias.

## Impacto en el dashboard

El [dashboard](feedlot/04-dashboard-metricas.md) suma un **desglose de costos por tipo**: alimentación, sanidad, mano de obra, maquinaria, combustible, fletes y otros. Muestra en qué se compone el costo del cliente, sin interpretarlo como margen.

## Reglas

- Mismo criterio de **precio histórico**: cada cargo guarda su `unit_price` y `quantity` del día.
- Misma **inmutabilidad**: un cargo mal hecho se corrige con contra-asiento, no se edita.

> Detalle para el repo: se agrega a las filas de glosario y a `API.md` la app `services`, `ServiceType`/`ServiceCharge` y sus endpoints; el `concept = service` ya está contemplado en el ADR-25 del ledger.
