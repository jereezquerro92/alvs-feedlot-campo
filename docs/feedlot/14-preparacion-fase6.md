# 14 · Preparación para Fase 6 (multi-rubro)

> No se construye ahora. Este documento deja anotado qué mirar cuando aparezca el **segundo rubro real**, para no rediseñar la columna vertebral bajo presión.

**Regla que ya se respetó:** la columna vertebral (`clients`, `ledger`, `market`, `advisors`) no conoce a ningún rubro. El ganadero (`livestock`, `feed`, `sanitary`, `metrics`) postea al ledger por el par genérico (`source_kind`, `source_id`). Un rubro nuevo entra por la misma puerta sin tocar lo hecho (adr-24, adr-25).

## Cuándo se dispara

Cuando haya un **segundo rubro concreto pedido** (caballos, alfalfa, taller), no antes. Extraer abstracciones con un solo caso es adivinar.

## Qué se extrae, y solo entonces

Los conceptos que ya se repetirán en dos rubros:

- **`Asset`** — un individuo o unidad con ciclo de vida (un caballo, un pivote de riego, una máquina). `Animal` y `Lot` son casos de esto, pero **no se refactorizan hacia atrás** salvo que duela: la regla es no romper lo que anda.
- **`Task`** — una labor con costo (una tarea de alfalfa, un service de máquina). Postea al ledger igual que `FeedingEvent`.
- **`MaintenanceEvent`** — para activos con mantenimiento (taller, maquinaria).

Se sacan a una app compartida `assets` **cuando el segundo rubro los necesite**, no antes.

## Lo que ya está listo para recibirlos

- El **ledger** cobra cualquier evento por (`source_kind`, `source_id`). Un `source_kind="field_task"` entra sin cambios en `ledger`.
- Las **métricas** (`apps.metrics`) son funciones sobre eventos; un rubro nuevo suma las suyas sin tocar las del ganadero.
- Los **asesores** reciben un snapshot; un asesor de otro rubro arma su propio snapshot y reusa el mismo `AdvisorReport`.
- Los **precios** (`market`) ya son multi-fuente por `slug`; un rubro con precios propios suma fuentes.

## Orden tentativo por afinidad

1. **Caballos (`equines`)** — casi idéntico a `livestock`; es el mejor primer caso para validar si conviene extraer `Asset` o copiar el patrón.
2. **Alfalfa y pivotes (`crops`)** — introduce `Asset` (pivote) + `Task` (labor) de forma más clara.
3. **Taller y maquinaria (`machinery`)** — introduce `MaintenanceEvent`.

## Señal de alarma

Si al construir el segundo rubro estás copiando y pegando más de dos modelos casi iguales de `livestock`, ese es el momento de extraer `assets` — ni antes (especulación) ni mucho después (deuda). El costo de esperar es una refactorización acotada; el de adelantarse es una abstracción equivocada.
