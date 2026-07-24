---
title: adr-32-multi-rubro-assets
type: adr
status: active
created: 2026-07-24
tags: [adr, feedlot, multi-rubro, assets, crops, machinery]
---

# ADR-32 — Multi-rubro: la extracción de `assets` y los rubros `crops` y `machinery`

**Estado:** propuesto (Fase 6)
**Contexto:** primer segundo-rubro real; dispara la extracción prevista en
[[14-preparacion-fase6]]. Extiende [[adr-24-feedlot-domain]] ("crece por adición"),
reusa el ledger de [[adr-25-account-ledger]] sin tocarlo y la restricción XOR de
[[adr-26-livestock-individual-and-lot]] como precedente de forma.

## Contexto

Hasta la Fase 5 el sistema conocía un solo rubro: la hacienda. El feedlot también
produce su propia alfalfa sobre pivotes de riego (círculos), la corta varias veces
por temporada, y sostiene maquinaria con sus mantenimientos. Cargar círculos,
cortes, tareas, máquinas y mantenimientos es el pedido de esta fase.

Construir crops y machinery copiando `Animal`/`Lot` y sus eventos habría duplicado
tres modelos casi iguales — la señal de alarma que [[14-preparacion-fase6]] fija
para extraer las abstracciones compartidas. Dos rubros nuevos a la vez es
exactamente el disparador: se saca lo común a una app `assets`, y recién ahí, no
antes (YAGNI: no se extrajo en la Fase 1 con un solo rubro).

## Decisiones

### 1. `assets` aporta abstracciones, no tablas

`assets` no tiene modelos concretos ni migraciones de tablas propias: expone dos
bases abstractas — `AssetBase` (identidad + ciclo de vida de un activo) y
`CostedEvent` (un evento que fotografía `unit_price`×`quantity` y postea un débito
`service`). `crops` y `machinery` heredan de ellas.

*Por qué:* es el mismo idiom que ya usa `LifecycleEvent` en `livestock` (adr-28
regla 1): compartir la forma sin fusionar dominios. Un activo concreto vive en la
app de su rubro y mantiene su propia tabla; lo común no se paga dos veces.

### 2. `Animal`/`Lot` NO se refactorizan hacia atrás

La hacienda existente no se reescribe para heredar de `AssetBase`. La extracción
mira hacia adelante: cubre los rubros nuevos, no migra el que ya funciona.

*Por qué:* reescribir modelos con datos, migraciones y tests que ya pasan, sólo por
simetría, es riesgo sin retorno. El precedente de forma (adr-26) alcanza; la
herencia literal no aporta nada que justifique tocar el dominio estable.

### 3. El costeo entra por el par genérico, sin cambiar `ledger`

`FieldTask` (tarea) y `MaintenanceEvent` (mantenimiento) postean un `debit` con el
`Concept.SERVICE` **ya existente**, vía `post_entry(...)` con
`source_kind ∈ {"field_task","maintenance_event"}` y `source_id` del evento — el par
`(source_kind, source_id)` de [[adr-24-feedlot-domain]] regla 4. `ledger` no gana
un modelo, un concepto ni un FK por rubro.

*Por qué:* es la costura de escalabilidad que la doctrina reservó justo para esto.
Un rubro nuevo que cobra no toca `ledger`; el seam ya estaba puesto desde la Fase 1.

### 4. El corte no toca el ledger; la tarea y el mantenimiento sí

`Cutting` (corte) es un evento de producción inmutable: registra kilos cosechados,
no postea asiento. `FieldTask` y `MaintenanceEvent` son costos: siempre postean.

*Por qué:* un corte no es un insumo entregado a un cliente, es cosecha propia — no
hay a quién cobrarle. El ledger cobra insumos entregados (adr-25 regla 6, mismo
criterio que deja a `Weighing`/`Death` sin asiento). Puentear un corte al stock de
alimento propio (`FeedStockMovement`) es una adición futura explícita, no parte de
esta fase: se agrega cuando el negocio lo pida, con su propio cambio.

### 5. Toda tarea y todo mantenimiento cobran a un cliente

`FieldTask` y `MaintenanceEvent` llevan `client` obligatorio y siempre postean.
El feedlot propio es un `Client(kind=own)`; sus costos internos se acumulan en esa
cuenta, igual que su hacienda propia ya lo hace.

*Por qué:* modelar un origen "sin cliente / sin cargo" que hoy no se usa es
complejidad especulativa (mismo criterio que adr-28 regla 5 para sanidad). Si mañana
una tarea se hace como servicio a un tercero, el `client` ya lo contempla sin
cambiar el modelo.

### 6. Los activos son catálogos editables; los eventos son inmutables

`Pivot`, `Machine` y `Crop` son datos maestros: ModelViewSet con CRUD completo
("cargar círculos" es crear pivotes). `Cutting`, `FieldTask` y `MaintenanceEvent`
son eventos operativos: list/retrieve/create, sin update ni destroy (adr-24 regla 3).

*Por qué:* un activo tiene estado que se corrige (se da de baja un pivote, se
renombra una máquina); un evento operativo es un hecho fechado que sólo se corrige
con otro evento, nunca editando el pasado.

### 7. Categorías, estados y especies son `choices` en inglés

`species`, `category`, `kind`, `status` son enums en inglés ([[LOCALIZATION]]); el
español vive sólo en el render del frontend.

## Consecuencias

- Las métricas de costo existentes (`cost_breakdown` suma débitos por `concept`) ya
  recogen las tareas y mantenimientos como `service` sin tocar `apps.metrics`: el
  rubro nuevo compone, no reforma.
- Un pivote o máquina dado de baja (`status=retired`) rechaza eventos nuevos en el
  servicio, no en la vista — misma postura que un animal muerto (adr-28).
- `assets` queda como el hogar de la próxima abstracción compartida (equinos u otro
  rubro entran heredando, no copiando). La extracción se hizo una vez y para todos.
- Cualquier cambio a las reglas 1–5 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
