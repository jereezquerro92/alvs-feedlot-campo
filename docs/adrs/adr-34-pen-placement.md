---
title: adr-34-pen-placement
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, feedyard, pens, placement, phase-7b]
---

# ADR-34 — Ubicación de hacienda en corrales (`PenPlacement`)

**Estado:** activo (Fase 7b)
**Contexto:** completa el diferimiento de [[adr-33-feedyard-operating-loop]] decisión 7
(el cierre por corral necesita saber qué hacienda estuvo en el corral). Reusa la
restricción XOR animal/lote de [[adr-26-livestock-individual-and-lot]] y la postura
event-sourced de [[adr-24-feedlot-domain]]. Reglas solamente; las entidades viven en
[[FEEDLOT-DATA-MODEL]].

## Contexto

La Fase 7 dio el corral (`Pen`), la receta (`Ration`), el plan (`LoadingOrder`) y la
lectura de comedero (`BunkScore`), pero no dónde está cada animal. Sin eso, el corral
es un rótulo sobre el `FeedingEvent` y nada más: no hay ocupación, no hay cabezas por
corral, no hay base para un cierre por corral. Se agrega el hecho que faltaba —
**dónde está la hacienda** — sin tocar cómo se cobra ni reescribir el dominio estable.

## Decisiones

### 1. La ubicación es un evento inmutable, no un campo de estado

`PenPlacement` registra un movimiento fechado de un `Animal` o un `Lot` hacia adentro
(`direction=in`) o hacia afuera (`direction=out`) de un `Pen`. La ubicación actual y
la ocupación se **derivan** de esos eventos; nunca se guardan como un campo editable
en `Pen` ni en `Animal` (misma postura que adr-24 regla 3, adr-26 regla 4).

*Por qué:* un feedlot mueve hacienda entre corrales todo el tiempo. Un campo
`Animal.pen` mutable perdería la historia — de qué corral vino, cuánto estuvo. El
evento la conserva y hace auditable el cierre por corral.

### 2. Exactamente un target, a nivel base de datos

Un `PenPlacement` apunta a un `Animal` O a un `Lot`, nunca ambos ni ninguno —
`CHECK` constraint con dos FK nulables, idéntico al de los eventos de ciclo de vida
(adr-26 regla 3). Para un animal individual el movimiento es de una cabeza; para un
lote, `head_count` permite mover una parte.

*Por qué:* reusar la forma ya probada evita una tabla polimórfica y mantiene la
consulta directa. Un lote se mueve parcialmente en la práctica; el animal no se
fracciona.

### 3. No toca el ledger

`PenPlacement` no postea ningún asiento. Mover hacienda de corral no es un insumo
entregado ni un cargo — es logística interna. El cobro sigue exclusivamente en `feed`
(adr-25 regla 4), como todo el resto de `feedyard` (adr-33 decisión 1).

*Por qué:* un solo camino de cobro. La ubicación es información de gestión, no un
hecho económico.

### 4. Un corral inactivo y un animal no-activo rechazan el ingreso, en el servicio

`register_placement` rechaza en el **servicio** (no en la vista) un `Pen` con
`status=inactive` y un `Animal` que no esté `active` (muerto/vendido/salido no se
ubica). La carga tardía con fecha retroactiva se acepta mientras el corral siga
activo — misma regla que adr-28 para pesajes y sanidad.

*Por qué:* las reglas de negocio viven en el servicio, único punto de escritura, para
que la vista, el admin y un comando compartan la misma validación.

### 5. El cierre por corral de esta fase es ocupación, no ganancia

`apps.metrics` gana un reporte por corral: ocupación actual (cabezas), cabezas
ingresadas/egresadas en el período y kilos alimentados al corral. La **conversión por
corral** (kg producidos ÷ kg alimentados) sigue diferida: atribuir pesajes al tramo
que un animal pasó en un corral es un problema aparte, y un número sin esa atribución
sería inventado (adr-29 regla 2). Se entrega lo afirmable hoy; la conversión por
corral entra cuando la atribución exista.

*Por qué:* honestidad de la métrica. La ocupación se puede afirmar desde los eventos
de placement; la conversión por corral no, todavía.

## Consecuencias

- El backend entra sólo por [[API]] (adr-03) y nace por el flujo [[TDD]] (adr-07).
- La única migración es la tabla nueva `PenPlacement` en `feedyard`; nada fuera de la
  app, nada en `ledger`.
- `Pen` sigue sin FK a cliente: un corral puede alojar hacienda de varios clientes, y
  el placement es quien liga cada cabeza a su corral y su dueño (vía el animal/lote).
- Cualquier cambio a las reglas 1–5 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
