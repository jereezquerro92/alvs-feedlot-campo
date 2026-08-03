---
title: ADR-46 — Cría y recría: los eventos reproductivos (breeding)
type: adr
status: active
created: 2026-07-28
tags: [adr, feedlot, breeding, livestock, reproduction, event-sourced, phase-breeding]
---

# ADR-46 — Cría y recría: los eventos reproductivos (`breeding`)

**Contexto:** crece por adición sobre la espina ([[adr-49-domain-layer-and-growth-by-addition]] regla 1): una app
nueva `breeding`, sin tocar `livestock` ni el ledger salvo el único cargo que el dueño
definió. Reusa la restricción XOR animal/lote de [[adr-26-livestock-individual-and-lot]] y
el abstracto `LifecycleEvent` de [[adr-28-animal-lifecycle-and-sanitary]] decisión 1; el
idiom plantilla→calendario relativo de [[adr-40-sanitary-plan-schedule]] para el protocolo
IATF; el contrato del "no calculable" de [[adr-29-metrics-derivation]] para las métricas; y
el par genérico `(source_kind, source_id)` de [[adr-49-domain-layer-and-growth-by-addition]] regla 4 para el
único asiento. Depende de [[adr-47-genetics-semen-embryo]] para toros, semen y embriones.
Reglas solamente; las entidades viven en [[FEEDLOT-DATA-MODEL]], los nombres en
[[GLOSSARY]] (`GLOSSARY-feedlot-additions.md`) antes de su primer uso
([[adr-01-glossary-and-localization]]).

## Contexto

Hasta hoy el sistema conoce al animal entrando, comiendo, engordando, enfermando y
saliendo, pero no lo conoce **reproduciéndose**. Falta el corazón de un rodeo de cría: el
ciclo `servicio → tacto → parición → destete`, del que salen las métricas que justifican el
rubro (% preñez, % parición, % destete, IEP, kg destetados por vientre). La recría —engordar
al destetado hasta peso objetivo— **ya está casi toda hecha**: reusa `Weighing`/GDP, `feed`,
`sanitary` y el placement en corral. Lo genuinamente nuevo es la reproducción. Se agrega la
app `breeding` con esos cuatro hechos, sin reescribir el dominio estable.

## Decisiones

### 1. `breeding` son eventos reproductivos inmutables; casi nada toca el ledger

`breeding` no tiene catálogos de negocio propios más allá del protocolo IATF (decisión 5):
son cuatro eventos fechados. Ninguno postea un asiento **salvo** el cargo de servicio de IA
sobre hacienda de cliente (decisión 6). El cobro de alimento y sanidad sigue exclusivamente
en `feed` y `sanitary` ([[adr-25-account-ledger]], [[adr-28-animal-lifecycle-and-sanitary]]).

*Por qué:* un solo camino de cobro. La reproducción es sobre todo un registro de gestión;
el único hecho económico que el dueño definió es el servicio de inseminación facturado.

### 2. Cuatro eventos, cada uno target `Animal` XOR `Lot`, a nivel base de datos

`Service`, `PregnancyCheck`, `Calving` y `Weaning` heredan de `LifecycleEvent`
([[adr-28-animal-lifecycle-and-sanitary]] decisión 1): el par `animal`/`lot` con `CHECK` de
exactamente uno ([[adr-26-livestock-individual-and-lot]] regla 3). Cada uno mantiene su
tabla y expone `list`/`retrieve`/`create`, sin `update` ni `destroy`
([[adr-49-domain-layer-and-growth-by-addition]] regla 3). El servicio individual es sobre una vaca; el IATF
sistemático se carga sobre un `Lot` (un rodeo servido junto).

*Por qué:* reusar la forma ya probada evita una tabla polimórfica y mantiene la consulta
directa. Los cuatro necesitan idénticamente "exactamente un target".

### 3. El estado reproductivo se DERIVA de los eventos, nunca se guarda

`vacía` / `servida` / `preñada` / `parida` / `seca` no es un campo editable en `Animal` ni
en ningún lado: se deriva cruzando los `Service`, `PregnancyCheck` y `Calving` de cada
vientre ([[adr-49-domain-layer-and-growth-by-addition]] regla 3). El diagnóstico de preñez vigente es el último
`PregnancyCheck`; la preñez se cierra con el `Calving` correspondiente.

*Por qué:* un flag reproductivo mutable se desincroniza de los hechos. Derivarlo garantiza
que el estado y los eventos no puedan contradecirse — son la misma fuente.

### 4. La parición crea el ternero; la genealogía se deriva, sin tocar `Animal`

Un `Calving` de resultado `live` sobre una vaca individual **crea** un `Animal`
(`category=calf`) y lo referencia en `Calving.calf` (FK nullable). La madre es el target del
parto (`Calving.animal`), el padre es el toro del servicio que confirmó la preñez
(`Calving.service → Service.sire`, [[adr-47-genetics-semen-embryo]]). La genealogía se
**deriva** de esa cadena; **no** se agrega ningún campo `dam`/`sire` a `Animal` —la
extracción mira hacia adelante ([[adr-32-multi-rubro-assets]] regla 2,
[[adr-38-senasa-traceability]] precedente de la caravana). Un `Calving` sobre un `Lot`
registra `births_count` y suma cabezas al lote de terneros, sin crear identidad por cabeza
([[adr-26-livestock-individual-and-lot]] regla 1).

*Por qué:* `Intake` ya crea `Animal`s, así que un evento que engendra un animal tiene
precedente. Derivar la genealogía en vez de denormalizarla en `Animal` mantiene `livestock`
estable y hace la parentela auditable desde el hecho que la produjo.

### 5. El protocolo IATF es una plantilla editable con calendario relativo

`IatfProtocol` + `IatfProtocolStep` son datos maestros: ModelViewSet con CRUD completo
—"cargar un protocolo" es crear el protocolo y sus pasos (día 0 dispositivo, día 7
prostaglandina, etc.)—. Cada paso fija un `day_offset` relativo; la fecha absoluta de cada
paso se **deriva** del `Service.date` de la inseminación que referencia el protocolo, nunca
se guarda en la plantilla. Mismo idiom que `SanitaryPlan`/`SanitaryPlanItem`
([[adr-40-sanitary-plan-schedule]] decisiones 1–2).

*Por qué:* un protocolo es "a los N días de arrancar"; guardar fechas absolutas lo ataría a
un solo servicio. El offset relativo lo hace reusable, que es el punto de una plantilla.

### 6. Solo la IA/IATF sobre hacienda de cliente cobra; el resto no postea

Un `Service` con `method ∈ {ai, iatf}` sobre hacienda de un `Client(kind=boarding)` postea
**un `debit` `concept=service`** a la cuenta del cliente, por la tarifa de inseminación, vía
el par genérico `(source_kind="breeding_service", source_id=<Service.id>)`
([[adr-49-domain-layer-and-growth-by-addition]] regla 4). Fotografía `service_price` (la tarifa) del día
([[adr-25-account-ledger]] regla 3). El servicio `natural`, el servicio sobre hacienda
propia, y los eventos `PregnancyCheck`, `Calving` y `Weaning` **no** postean asiento. El
costo del semen consumido lo maneja `genetics` como un `out` de stock, no como un cargo acá
([[adr-47-genetics-semen-embryo]] decisión 6).

*Por qué:* el dueño definió exactamente un hecho económico en la reproducción —la IA
facturada al cliente boarding— y ninguno más. Modelar un cargo por tacto o por parición que
hoy no se factura es complejidad especulativa (mismo criterio que
[[adr-28-animal-lifecycle-and-sanitary]] decisión 5); si mañana se cobra el tacto, entra por
el mismo seam con su propio cambio.

### 7. El servicio consume genética y valida en el servicio, no en la vista

`register_service` descuenta un `SemenMovement` `out` del `SemenBatch` para `method ∈
{ai, iatf}`, y un `EmbryoMovement` `out` del `EmbryoBatch` para `method=embryo_transfer`
([[adr-47-genetics-semen-embryo]]). Rechaza en el **servicio**: un target no activo
(muerto/vendido/egresado no se sirve), un target ajeno al cliente, la ausencia del XOR
exacto, un `SemenBatch`/`EmbryoBatch` sin stock o inactivo, y un `IatfProtocol` inactivo. La
carga tardía con fecha retroactiva se acepta mientras el target siga activo —misma norma de
campo que [[adr-28-animal-lifecycle-and-sanitary]].

*Por qué:* las reglas de negocio viven en el servicio, único punto de escritura, para que
vista, admin y comando compartan la misma validación.

### 8. Las métricas reproductivas se derivan en `apps.metrics`, honestas con el hueco

`apps.metrics` gana, como funciones puras sobre los eventos ([[adr-29-metrics-derivation]]
regla 1): `pregnancy_rate` (% preñez = preñadas/servidas), `calving_rate` (% parición =
paridas/preñadas), `weaning_rate` (% destete = destetados/paridos), `calving_interval` (IEP,
días promedio entre partos por vientre) y `kg_weaned_per_dam`. Cada una devuelve `null` con
su `not_calculable` (`no_services_in_period`, `no_pregnancy_checks`, `no_calvings`, …)
cuando falta el insumo, nunca un cero de relleno ([[adr-29-metrics-derivation]] regla 2).

*Por qué:* un "% preñez = 0" y un "no hubo servicios que evaluar" son situaciones opuestas;
el cero las confunde, el hueco explícito las distingue y le dice al operador qué medir.

### 9. La recría no gana app: reusa lo existente más un `Weaning` con destino

El destetado sigue siendo un `Animal` normal: su recría se mide con `Weighing`/GDP, se
alimenta con `feed`, se sanea con `sanitary` y se ubica con `PenPlacement` —nada nuevo. El
único agregado de recría es el `Weaning` (peso y fecha del destete) con un `purpose`
(`replacement` | `sale` | `undecided`) que marca la selección de vaquillonas de reposición.

*Por qué:* la recría es engorde de un animal ya modelado; crear una app paralela duplicaría
`livestock`/`feed` sin agregar un hecho nuevo. El destete es el único hito que faltaba.

## Consecuencias

- El backend entra solo por [[API]] ([[adr-03-api-and-backend]]) y nace por el flujo [[TDD]]
  ([[adr-07-development-flow]]); este ADR no exceptúa ese camino
  ([[adr-49-domain-layer-and-growth-by-addition]] regla 6).
- Migraciones: las tablas nuevas viven en `breeding` (`Service`, `PregnancyCheck`,
  `Calving`, `Weaning`, `IatfProtocol`, `IatfProtocolStep`) y una FK nullable `calf` de
  `Calving` a `livestock.Animal`. Nada fuera de la app nueva; nada en `ledger` (el débito de
  IA reusa `Concept.SERVICE` por el seam, sin modelo ni concepto nuevo).
- La app `advisors`/`assistant` ganan estas métricas sin cambiar su código: leen
  `apps.metrics` ([[adr-29-metrics-derivation]] regla 1, [[adr-31-advisors-implementation]]
  decisión 3).
- `ASSISTANT`/`ADVISOR` y demás variables no cambian: `breeding` no agrega credenciales ni
  servicios externos.
- El gateo RBAC de estas rutas se declara en [[API]] con su clase de permiso antes del
  código ([[adr-44-field-operational-roles]] decisión 7): la carga reproductiva es de
  `field_managers` (y `feed_operators` donde aplique), la lectura sigue las reglas del rol.
- Cualquier cambio a las reglas 1–9 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
