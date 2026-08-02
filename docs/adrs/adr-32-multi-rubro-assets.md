---
title: adr-32-multi-rubro-assets
type: adr
category: backend
use_case: agregar un rubro nuevo, cargar pivotes, cortes, máquinas o mantenimientos, heredar de las bases de assets, costear un evento que no es hacienda
created: 2026-07-24
modified: 2026-08-02
tags: [adr, feedlot, multi-rubro, assets, crops, machinery]
---

# ADR-32 — Multi-rubro: la extracción de `assets` y los rubros `crops` y `machinery`

## CONTEXT

> El primer segundo rubro real: alfalfa sobre pivotes y maquinaria con sus mantenimientos. Dos rubros a la vez son el disparador para extraer lo común a `assets`, y ese es el momento — no antes, con un solo rubro, y no hacia atrás sobre la hacienda que ya funciona.

## ASSERTIONS

1. `assets` aporta abstracciones y no tablas: expone `AssetBase` (identidad y ciclo de vida de un activo) y `CostedEvent` (un evento que fotografía `unit_price × quantity` y postea un débito `service`). `crops` y `machinery` heredan de ellas y cada activo concreto mantiene su propia tabla, mismo idiom que `LifecycleEvent` en `livestock` ([[adr-28-animal-lifecycle-and-sanitary]] regla 1).
2. `Animal` y `Lot` no se refactorizan hacia atrás. La extracción mira hacia adelante: cubre los rubros nuevos, no migra el que ya funciona con datos, migraciones y tests que pasan.
3. El costeo entra por el par genérico: `FieldTask` y `MaintenanceEvent` postean un `debit` con el `Concept.SERVICE` existente, vía `post_entry` con `source_kind ∈ {"field_task", "maintenance_event"}` ([[adr-24-feedlot-domain]] regla 4). `ledger` no gana un modelo, un concepto ni un FK por rubro.
4. `Cutting` es un evento de producción inmutable —registra kilos cosechados y no postea asiento, porque una cosecha propia no es un insumo entregado a un cliente—. `FieldTask` y `MaintenanceEvent` son costos y siempre postean.
5. Toda tarea y todo mantenimiento llevan `client` obligatorio. El feedlot propio es un `Client(kind=own)` y sus costos internos se acumulan en esa cuenta, igual que su hacienda propia.
6. `Pivot`, `Machine` y `Crop` son catálogos editables con CRUD completo; `Cutting`, `FieldTask` y `MaintenanceEvent` son eventos: `list`/`retrieve`/`create`, sin `update` ni `destroy` ([[adr-24-feedlot-domain]] regla 3). Un pivote o máquina `retired` rechaza eventos nuevos en el servicio, no en la vista.
7. `species`, `category`, `kind` y `status` son enums en inglés ([[LOCALIZATION]]); el español vive sólo en el render.

## FORBIDDEN

- **NEVER** copiar `Animal`/`Lot` y sus eventos para un rubro nuevo (regla 1). Tres modelos casi iguales son la señal que dispara la extracción, no una forma de avanzar.
- **NEVER** reescribir la hacienda para que herede de `AssetBase` (regla 2). Es riesgo sin retorno sobre un dominio estable, sólo por simetría.
- **NEVER** agregar a `ledger` un modelo, un concepto o un FK para un rubro nuevo (regla 3). La costura genérica existe exactamente para que un rubro que cobra no lo toque.
- **NEVER** postear un asiento por un corte (regla 4). Es cosecha propia: no hay a quién cobrarle.
- **NEVER** validar el estado de un activo en la vista (regla 6). La regla de negocio vive en el servicio, único punto de escritura que comparten vista, admin y comando.

## REJECTED

- **Extraer `assets` en la Fase 1** — las abstracciones compartidas desde el principio, con un solo rubro. No se hizo por YAGNI: con un rubro no hay nada común que compartir, y la abstracción habría sido una conjetura sobre el segundo.
- **Un origen "sin cliente / sin cargo" para tareas y mantenimientos** — un evento que no cobra a nadie. Rechazado como complejidad especulativa (mismo criterio que [[adr-28-animal-lifecycle-and-sanitary]] sobre sanidad): el `Client(kind=own)` ya absorbe los costos internos.
- **Puentear el corte al stock de alimento propio** — un `Cutting` produciendo un `in` de `FeedStockMovement`. Postergado explícitamente: entra cuando el negocio lo pida, con su propio cambio, no como efecto lateral de esta fase.

## RELATED

### related adrs

- [[docs/adrs/adr-24-feedlot-domain]] — reglas 3 y 4, el crecimiento por adición y la costura de costeo
- [[docs/adrs/adr-25-account-ledger]] — qué cobra el ledger y qué no
- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — el idiom del abstracto y el criterio anti-especulativo
- [[docs/adrs/adr-37-inventory-and-weather]] — la misma extracción, aplicada al stock de insumos

### related files

- [[docs/feedlot/14-preparacion-fase6]] — la señal de alarma que dispara la extracción
- [[docs/FEEDLOT-DATA-MODEL]] — `Pivot`, `Machine`, `Crop`, `Cutting`, `FieldTask`, `MaintenanceEvent`
- [[docs/LOCALIZATION]] — inglés en el código, español en el render
