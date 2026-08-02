---
title: adr-46-breeding-reproduction
type: adr
category: backend
use_case: registrar un servicio, un tacto, una parición o un destete, cargar un protocolo IATF, leer métricas reproductivas, cobrar una inseminación
created: 2026-07-28
modified: 2026-08-02
tags: [adr, feedlot, breeding, livestock, reproduction, event-sourced]
---

# ADR-46 — Cría y recría: los eventos reproductivos (`breeding`)

## CONTEXT

> El ciclo servicio → tacto → parición → destete, que es el corazón de un rodeo de cría y del que salen % preñez, % parición, % destete e IEP. La recría no necesita app: engordar al destetado ya está modelado. Lo genuinamente nuevo es la reproducción.

## ASSERTIONS

1. `breeding` son cuatro eventos reproductivos inmutables y ninguno postea asiento salvo el cargo de IA sobre hacienda de cliente (regla 6). El cobro de alimento y sanidad sigue en `feed` y `sanitary`.
2. `Service`, `PregnancyCheck`, `Calving` y `Weaning` heredan de `LifecycleEvent` ([[adr-28-animal-lifecycle-and-sanitary]] regla 1): el par `animal`/`lot` con `CHECK` de exactamente uno ([[adr-26-livestock-individual-and-lot]] regla 3). Cada uno mantiene su tabla y expone `list`/`retrieve`/`create`, sin `update` ni `destroy`. El servicio individual es sobre una vaca; el IATF sistemático se carga sobre un `Lot`.
3. El estado reproductivo —vacía, servida, preñada, parida, seca— se deriva cruzando los servicios, tactos y pariciones de cada vientre, y no se guarda en ningún campo. El diagnóstico vigente es el último `PregnancyCheck`, y la preñez se cierra con su `Calving`.
4. Un `Calving` de resultado `live` sobre una vaca individual crea un `Animal` (`category=calf`) y lo referencia en `Calving.calf`. La genealogía se deriva de esa cadena —madre por el target, padre por el toro del servicio— y no se agregan campos `dam`/`sire` a `Animal` ([[adr-32-multi-rubro-assets]] regla 2). Un `Calving` sobre un `Lot` registra `births_count` sin crear identidad por cabeza.
5. `IatfProtocol` y `IatfProtocolStep` son catálogos editables con CRUD completo; cada paso fija un `day_offset` relativo y la fecha absoluta se deriva del `Service.date`, nunca se guarda en la plantilla. Mismo idiom que [[adr-40-sanitary-plan-schedule]] reglas 1–2.
6. Un `Service` con `method ∈ {ai, iatf}` sobre hacienda de un `Client(kind=boarding)` postea un `debit` `concept=service` por la tarifa de inseminación, vía `(source_kind="breeding_service", source_id=<Service.id>)` ([[adr-24-feedlot-domain]] regla 4), fotografiando `service_price` del día. El servicio natural, el servicio sobre hacienda propia, y los tactos, pariciones y destetes no postean nada.
7. `register_service` descuenta un `SemenMovement` `out` para `ai`/`iatf` y un `EmbryoMovement` `out` para `embryo_transfer` ([[adr-47-genetics-semen-embryo]]). Rechaza en el servicio un target no activo o ajeno al cliente, la ausencia del XOR exacto, una partida sin stock o inactiva y un protocolo inactivo. La carga tardía con fecha retroactiva se acepta mientras el target siga activo.
8. `apps.metrics` deriva `pregnancy_rate`, `calving_rate`, `weaning_rate`, `calving_interval` y `kg_weaned_per_dam` como funciones puras ([[adr-29-metrics-derivation]] regla 1). Cada una devuelve `null` con su `not_calculable` cuando falta el insumo, nunca un cero de relleno.
9. La recría no gana app: el destetado es un `Animal` normal que se mide con `Weighing`, se alimenta con `feed`, se sanea con `sanitary` y se ubica con `PenPlacement`. El único agregado es el `Weaning`, con su `purpose` (`replacement` | `sale` | `undecided`).

## FORBIDDEN

- **NEVER** guardar el estado reproductivo como campo (regla 3). Un flag mutable se desincroniza de los eventos que lo producen.
- **NEVER** agregar `dam`/`sire` a `Animal` (regla 4). La genealogía se deriva de la cadena parición → servicio, y `livestock` no se toca.
- **NEVER** guardar fechas absolutas en un `IatfProtocol` (regla 5). Lo ataría a un solo servicio y dejaría de ser plantilla.
- **NEVER** cobrar un tacto, una parición o un destete (regla 6). El dueño definió exactamente un hecho económico en la reproducción, y modelar otro es especulativo.
- **NEVER** servir un target no activo o de otro cliente (regla 7). La validación vive en el servicio, único punto de escritura.
- **NEVER** devolver 0% de preñez cuando no hubo servicios (regla 8). Son situaciones opuestas y el hueco explícito las distingue.

## REJECTED

- **Una app de recría** — un dominio paralelo para engordar al destetado. Rechazado por la regla 9: duplicaría `livestock` y `feed` sin agregar un hecho nuevo; el destete era el único hito que faltaba.
- **Cobrar el semen consumido como cargo del servicio** — debitar la pajuela además de la tarifa. No: el consumo propio es un `out` de stock ya valuado ([[adr-47-genetics-semen-embryo]] regla 6), y el único cargo es el servicio facturado.
- **Un modelo polimórfico para los cuatro eventos** — una tabla reproductiva con tipo. Rechazado por el mismo motivo que en [[adr-28-animal-lifecycle-and-sanitary]]: nulables en todas las filas y un filtro por tipo en cada consulta.

## RELATED

### related adrs

- [[docs/adrs/adr-47-genetics-semen-embryo]] — los toros, el semen y los embriones que el servicio consume
- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — regla 1, el abstracto `LifecycleEvent`
- [[docs/adrs/adr-26-livestock-individual-and-lot]] — regla 3, el XOR animal/lote
- [[docs/adrs/adr-40-sanitary-plan-schedule]] — el idiom plantilla + calendario relativo
- [[docs/adrs/adr-29-metrics-derivation]] — el contrato del "no calculable"
- [[docs/adrs/adr-44-field-operational-roles]] — el gateo RBAC de estas rutas

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `Service`, `PregnancyCheck`, `Calving`, `Weaning`, `IatfProtocol`
- [[docs/GLOSSARY-feedlot-additions]] — los nombres reproductivos, antes del primer uso
- [[docs/API]] — las rutas de `breeding`
