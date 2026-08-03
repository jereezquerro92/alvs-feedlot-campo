---
title: adr-40-sanitary-plan-schedule
type: adr
category: backend
use_case: cargar un plan sanitario o sus dosis, inscribir un animal o lote, leer qué vacuna está pendiente, tocar el calendario derivado
created: 2026-07-25
modified: 2026-08-02
tags: [adr, feedlot, sanitary, vaccination, plan, schedule, phase-13]
---

# ADR-40 — El plan sanitario y el calendario de vacunación

## CONTEXT

> El plan es intención a futuro —qué vacuna toca y cuándo— y el `HealthEvent` es un hecho pasado. Son cosas distintas y no se colapsan: el plan programa, el evento aplica y cobra, y el pendiente sale de cruzar los dos.

## ASSERTIONS

1. `SanitaryPlan` y `SanitaryPlanItem` son catálogos editables con CRUD completo: "cargar un plan" es crear el plan y sus dosis. `PlanEnrollment` —inscribir un animal o lote con una fecha de inicio— es un hecho fechado: `list`/`retrieve`/`create`, sin `update` ni `destroy` ([[adr-24-feedlot-domain]] regla 3). Mismo idiom que `Ration`/`LoadingOrder`: la receta se edita, la ejecución es inmutable.
2. Cada `SanitaryPlanItem` fija un `HealthProduct` y un `day_offset` en días desde el `start_date` de la inscripción. El vencimiento se deriva por inscripción y nunca se guarda como fecha absoluta en la plantilla, que es lo que hace al plan reusable.
3. El estado de cada dosis se deriva y no se persiste: está **aplicada** cuando existe un `HealthEvent` del mismo target y producto con fecha ≥ `start_date`; si no, está **pendiente** cuando su vencimiento ya pasó y **próxima** cuando todavía no. Sin inscripciones el calendario es una lista vacía, nunca un estado inventado ([[adr-29-metrics-derivation]] regla 2).
4. Ningún modelo de esta fase postea un asiento. El cobro sanitario sigue siendo exclusivamente del `HealthEvent` vía `register_health_event` ([[adr-28-animal-lifecycle-and-sanitary]] regla 5): un plan es intención y una inscripción un compromiso de calendario, y el cargo aparece cuando la dosis se aplica de verdad.
5. `enroll_in_plan` rechaza en el servicio —no en la vista— un plan inactivo, un target que no pertenece al cliente, un target no activo y la ausencia del XOR exacto. La carga tardía con fecha retroactiva se acepta mientras el target siga activo.
6. Una `PlanEnrollment` apunta a un `Animal` o a un `Lot`, nunca ambos ni ninguno: `CHECK` con dos FK nulables, idéntico al de los eventos de ciclo de vida ([[adr-26-livestock-individual-and-lot]] regla 3).
7. El calendario derivado es un `GET` de sólo lectura —la acción `schedule` del viewset de inscripciones— computado en la lectura. `HealthEvent` no se refactoriza: el estado "aplicada" se deriva mirando los eventos existentes, sin agregarle campo ni FK ([[adr-32-multi-rubro-assets]] regla 2). No se lleva stock sanitario en esta fase.

## FORBIDDEN

- **NEVER** persistir `applied`, `pending` o `upcoming` como flag (regla 3). El pendiente es una afirmación sobre la sanidad real del rodeo y sale de los hechos, no de un tilde que alguien se olvida de poner.
- **NEVER** guardar fechas absolutas en la plantilla (regla 2). Ataría el plan a un solo animal y dejaría de ser una plantilla.
- **NEVER** cobrar al inscribir (regla 4). Cobraría una vacuna que quizá nunca se aplica y reabriría el doble cargo que la doctrina cerró.
- **NEVER** editar una inscripción (regla 1). Es el hecho de que a ese lote se le arrancó ese plan tal día.
- **NEVER** validar la inscripción en la vista (regla 5). La regla vive en el servicio, que comparten vista, admin y comando.

## REJECTED

- **Colapsar el plan y el `HealthEvent`** — un solo modelo que sirva de programación y de aplicación, con un campo que diga si ya ocurrió. Rechazado porque mezcla intención y hecho: el evento se cobra y el plan no, y el flag reemplazaría la derivación de la regla 3.
- **Un flag `applied` en la dosis** — marcar la dosis como aplicada al cargar el evento. Perdió contra la regla 3: el calendario y lo efectivamente aplicado podrían contradecirse, que es justamente lo que derivar impide.
- **Stock sanitario en esta fase** — existencias además del calendario. Sigue sin tomarse, por el mismo motivo que en [[adr-28-animal-lifecycle-and-sanitary]]: el problema real de las vacunas es el vencimiento y la cadena de frío, no el saldo.

## RELATED

### related adrs

- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — el `HealthEvent` que cobra y contra el que se deriva el pendiente
- [[docs/adrs/adr-24-feedlot-domain]] — reglas 1 y 3, adición y evento inmutable
- [[docs/adrs/adr-26-livestock-individual-and-lot]] — regla 3, el XOR de la inscripción
- [[docs/adrs/adr-33-feedyard-operating-loop]] — el precedente plantilla editable / ejecución inmutable
- [[docs/adrs/adr-29-metrics-derivation]] — regla 2, nunca un estado de relleno

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `SanitaryPlan`, `SanitaryPlanItem`, `PlanEnrollment`
- [[docs/API]] — las rutas de planes, inscripciones y el calendario
