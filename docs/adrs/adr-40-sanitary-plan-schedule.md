---
title: adr-40-sanitary-plan-schedule
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, sanitary, vaccination, plan, schedule, phase-13]
---

# ADR-40 — El plan sanitario y el calendario de vacunación

**Contexto:** crece por adición sobre `sanitary` ([[adr-49-domain-layer-and-growth-by-addition]] regla 1),
reusa la restricción XOR animal/lote de [[adr-26-livestock-individual-and-lot]] y la
postura event-sourced de [[adr-49-domain-layer-and-growth-by-addition]] regla 3. Extiende
[[adr-28-animal-lifecycle-and-sanitary]] sin tocar el cobro que ese ADR fijó. Reglas
solamente; las entidades viven en [[FEEDLOT-DATA-MODEL]].

## Contexto

La Fase 2 dejó el `HealthEvent`: una aplicación puntual que ya ocurrió y que siempre
se cobra ([[adr-28-animal-lifecycle-and-sanitary]] decisión 5). Falta lo otro que todo
feedlot maneja: el **plan sanitario** — el calendario de qué vacuna/tratamiento toca
aplicar y cuándo, contra el cual se controla qué está **pendiente**. Un plan es
intención a futuro; un `HealthEvent` es un hecho pasado. Son cosas distintas y no se
colapsan. Se agrega la capa de planificación sanitaria a la app `sanitary`, sin tocar
cómo se cobra.

## Decisiones

### 1. El plan es una plantilla reusable editable; la inscripción es un evento inmutable

`SanitaryPlan` + `SanitaryPlanItem` son datos maestros: ModelViewSet con CRUD completo
— "cargar un plan" es crear el plan y sus dosis. `PlanEnrollment` (inscribir un animal
o lote a un plan con una fecha de inicio) es un hecho fechado: list/retrieve/create,
sin update ni destroy ([[adr-49-domain-layer-and-growth-by-addition]] regla 3).

*Por qué:* un plan tiene composición que se corrige (se agrega una dosis, se ajusta un
día); una inscripción es un hecho —"a este lote se le arrancó este plan tal día"— que
no se reescribe. Mismo idiom que `Ration`/`LoadingOrder` (adr-33): la receta se edita,
la ejecución es inmutable.

### 2. El calendario es relativo; el vencimiento se deriva, nunca se guarda

Cada `SanitaryPlanItem` fija un `HealthProduct` y un `day_offset` (días desde el
`start_date` de la inscripción). El vencimiento de una dosis se **deriva**
(`start_date + day_offset`) por inscripción; no se guarda una fecha absoluta en el
plan. Así un plan sirve para muchos targets, cada uno con su propia fecha de arranque.

*Por qué:* un calendario de vacunación es "a los N días de entrar"; guardar fechas
absolutas en la plantilla la ataría a un solo animal. El offset relativo hace el plan
reusable, que es todo el punto de una plantilla.

### 3. El estado de cada dosis se deriva cruzando el calendario con los `HealthEvent`

`applied` / `pending` / `upcoming` no se persiste en ningún lado. Se deriva: una dosis
está **aplicada** cuando existe un `HealthEvent` del mismo target y mismo producto con
fecha ≥ `start_date`; si no, está **pendiente** cuando su vencimiento ya pasó
(`due_date ≤ as_of`) y **próxima** cuando todavía no. Sin inscripciones, el calendario
es una lista vacía — nunca un cero de relleno ni un estado inventado (postura de
[[adr-29-metrics-derivation]] regla 2).

*Por qué:* el pendiente es una afirmación sobre la sanidad real del rodeo, y tiene que
salir de los hechos (los `HealthEvent`), no de un flag editable que alguien se olvida
de tildar. Derivarlo garantiza que el calendario y lo efectivamente aplicado no puedan
contradecirse — son la misma fuente.

### 4. Ni el plan ni la inscripción tocan el ledger

Ningún modelo de esta fase postea un asiento. El cobro sanitario sigue siendo
exclusivamente del `HealthEvent` vía `register_health_event`
([[adr-28-animal-lifecycle-and-sanitary]] decisión 5, [[adr-25-account-ledger]]). Un
plan es intención; una inscripción es un compromiso de calendario; ninguno es un insumo
entregado. El cargo aparece recién cuando la dosis se aplica de verdad y eso es un
`HealthEvent`.

*Por qué:* un solo camino de cobro. Cobrar al inscribir cobraría una vacuna que quizás
nunca se aplica, y reabriría la puerta al doble cargo que la doctrina cerró (un hecho se
afirma una vez, adr-49 regla 5).

### 5. La inscripción valida en el servicio, no en la vista

`enroll_in_plan` rechaza en el **servicio** un plan inactivo, un target que no pertenece
al cliente, un target no activo (muerto/vendido/egresado no se inscribe) y la ausencia
del XOR exacto animal/lote. La carga tardía con fecha retroactiva se acepta mientras el
target siga activo — misma norma de campo que adr-28.

*Por qué:* las reglas de negocio viven en el servicio, único punto de escritura, para
que vista, admin y comando compartan la misma validación.

### 6. Un solo target por inscripción, a nivel base de datos

Una `PlanEnrollment` apunta a un `Animal` O a un `Lot`, nunca ambos ni ninguno — `CHECK`
constraint con dos FK nulables, idéntico al de los eventos de ciclo de vida
([[adr-26-livestock-individual-and-lot]] regla 3, [[adr-28-animal-lifecycle-and-sanitary]]
decisión 1).

*Por qué:* reusar la forma ya probada evita una tabla polimórfica y mantiene la consulta
directa.

## Consecuencias

- El backend entra solo por [[API]] ([[adr-03-api-and-backend]]) y nace por el flujo
  [[TDD]] ([[adr-07-development-flow]]); este ADR no exceptúa ese camino.
- Las migraciones son tres tablas nuevas en `sanitary` (`SanitaryPlan`,
  `SanitaryPlanItem`, `PlanEnrollment`); nada fuera de la app, nada en `ledger`.
- El calendario derivado es un `GET` de solo lectura (acción `schedule` del viewset de
  inscripciones); se computa en la lectura, nunca se materializa como campo editable
  ([[adr-49-domain-layer-and-growth-by-addition]] regla 3).
- No se agregan variables de entorno: es dato interno, sin servicios externos.
- `HealthEvent` no se refactoriza: el estado "aplicada" se deriva mirando los eventos
  existentes, no se agrega un campo ni un FK al `HealthEvent` (la extracción mira hacia
  adelante, [[adr-32-multi-rubro-assets]] regla 2).
- No se lleva stock sanitario en esta fase (sigue vigente adr-28 decisión 6): el plan
  programa aplicaciones, no existencias.
- Cualquier cambio a las reglas 1–6 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
