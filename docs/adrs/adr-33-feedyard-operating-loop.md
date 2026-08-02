---
title: adr-33-feedyard-operating-loop
type: adr
category: backend
use_case: cargar un corral, una ración o una orden de carga, registrar una lectura de comedero, alimentar por corral, leer el cierre de costo por corral
created: 2026-07-25
modified: 2026-08-02
tags: [adr, feedlot, feedyard, pens, rations, bunk, phase-7]
---

# ADR-33 — El loop operativo del corral (`feedyard`)

## CONTEXT

> El ciclo diario de un feedlot —dieta, orden de carga, alimentar, leer el comedero, ajustar— vive en `feedyard`. Es la capa que planea y mide; el cobro se queda entero en `feed`.

## ASSERTIONS

1. Ningún modelo de `feedyard` postea un asiento. El cobro de alimento es exclusivamente de `feed` vía `register_feeding` ([[adr-25-account-ledger]] regla 4): `feedyard` planea (`LoadingOrder`), describe (`Ration`) y mide (`BunkScore`), y el cargo aparece cuando la ración se ejecuta.
2. La `LoadingOrder` es el plan —lo que el mixer debía llevar a un corral para una ración— y el `FeedingEvent` es lo ejecutado, con peso y precio reales, y lo único que cobra. No son el mismo hecho duplicado: su diferencia es el desvío plan-vs-real, que es el dato de gestión.
3. El `pen` en `FeedingEvent` es una FK nullable, aditiva y opcional. Los feedings sin corral siguen siendo válidos; el corral enriquece el feeding, no es una condición nueva para alimentar.
4. `Ration` y `RationLine` describen la composición —qué `FeedType`, en qué `proportion`, con qué `dry_matter_pct`— y no tienen precio propio: el costo aparece al servir, con el `unit_price` histórico del evento ([[adr-25-account-ledger]] regla 3). La materia seca vive en la receta porque el consumo técnico se mide en materia seca, no en tal cual.
5. `Pen`, `Ration` y `RationLine` son catálogos con CRUD completo; `LoadingOrder` y `BunkScore` son hechos fechados: `list`/`retrieve`/`create`, sin `update` ni `destroy` ([[adr-24-feedlot-domain]] regla 3).
6. `register_loading_order` y `register_bunk_score` rechazan en el servicio —no en la vista— un `Pen` con `status=inactive`, y una `LoadingOrder` rechaza una `Ration` inactiva. La carga tardía con fecha retroactiva se acepta mientras el corral siga activo.
7. `apps.metrics` deriva el cierre de costo por corral: kilos servidos y costo de alimento en el período, leídos de `FeedingEvent.pen`. El cierre por ganancia lo completa [[adr-42-pen-conversion-honest-cut]] sobre los eventos de [[adr-34-pen-placement]].
8. La escala 0–4 de `BunkScore` es el estándar de lectura de comedero. Su interpretación —subir, bajar o mantener la ración— es lógica de frontend y nunca se hardcodea acá como cobro ni como acción automática.

## FORBIDDEN

- **NEVER** postear un asiento desde `feedyard` (regla 1). Dos apps que puedan debitar la misma cuenta por el mismo alimento reabren el doble cargo que la doctrina cerró ([[adr-24-feedlot-domain]] regla 5).
- **NEVER** fusionar la orden de carga con el feeding (regla 2). Se pierde el desvío plan-vs-real, que es la métrica que dice si el comedero se está leyendo bien.
- **NEVER** hacer obligatorio el `pen` en un `FeedingEvent` (regla 3). Sería reescribir el dominio estable para acomodar información nueva.
- **NEVER** ponerle precio a una `Ration` (regla 4). Editar la receta reescribiría el costo del pasado.
- **NEVER** derivar una conversión por corral sin saber qué hacienda estuvo ahí (regla 7). Sería un número inventado, que es lo que [[adr-29-metrics-derivation]] regla 2 prohíbe.

## REJECTED

- **Cobrar desde la orden de carga** — debitar lo planificado en vez de lo servido. Rechazado por la regla 1: cobraría kilos que el mixer quizá no llevó, y pondría un segundo camino de cobro sobre la misma cuenta.
- **Una sola entidad para plan y ejecución** — la orden que se marca como cumplida y pasa a ser el feeding. Perdió contra la regla 2; el desvío deja de existir en cuanto los dos hechos son uno.
- **El cierre por ganancia en esta fase** — conversión por corral junto con el costo. Se difirió por honestidad de la métrica y lo levantó [[adr-42-pen-conversion-honest-cut]] una vez que `PenPlacement` dio la atribución que faltaba.

## RELATED

### related adrs

- [[docs/adrs/adr-25-account-ledger]] — regla 4, el único camino de cobro del alimento
- [[docs/adrs/adr-24-feedlot-domain]] — el crecimiento por adición y la inmutabilidad de los eventos
- [[docs/adrs/adr-34-pen-placement]] — dónde está la hacienda, la pieza que faltaba
- [[docs/adrs/adr-42-pen-conversion-honest-cut]] — la mitad de ganancia del cierre por corral
- [[docs/adrs/adr-29-metrics-derivation]] — el contrato del número que no se inventa

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `Pen`, `Ration`, `RationLine`, `LoadingOrder`, `BunkScore`
- [[docs/FEEDLOT]] — el loop diario en la operación
- [[docs/API]] — las rutas de `feedyard`
