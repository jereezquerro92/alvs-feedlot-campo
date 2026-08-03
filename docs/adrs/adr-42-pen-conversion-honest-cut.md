---
title: adr-42-pen-conversion-honest-cut
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, feedyard, metrics, conversion, pen, phase-4b]
---

# ADR-42 — Conversión por corral: el corte honesto

**Contexto:** levanta el diferimiento explícito de [[adr-33-feedyard-operating-loop]]
decisión 7 y [[adr-34-pen-placement]] decisión 5 (la conversión por corral quedaba
diferida porque "atribuir pesajes al tramo que un animal pasó en un corral es un
problema aparte"). Consume `PenPlacement` (adr-34), `growth_series`
([[adr-28-animal-lifecycle-and-sanitary]]) y `FeedingEvent.pen` (adr-33 decisión 3).
Es una **adición** a `apps.metrics`, no una supersesión: la regla que prohíbe el
número inventado ([[adr-29-metrics-derivation]] regla 2) sigue intacta — este corte
la cumple, no la relaja. Reglas solamente; las funciones viven en `apps.metrics`.

## Contexto

El cierre por corral tenía dos mitades. La del **costo** (kilos servidos y costo de
alimento por corral) ya se entregó como `pen_cost_summary`/`pen_occupancy_report`:
se deriva de `FeedingEvent.pen` y de los eventos de `PenPlacement`, y es afirmable.
La de la **ganancia** —conversión = kg alimentados ÷ kg producidos en el corral— se
difirió porque un kilo de engorde no sabe en qué corral se puso: atribuirlo sin saber
dónde estuvo el animal fabrica el número que adr-29 regla 2 prohíbe.

La pieza que faltaba —`PenPlacement`, dónde estuvo cada cabeza y cuándo— ya existe
desde la Fase 7b. Con ella se puede atribuir **el subconjunto honesto**: los tramos
de pesaje que un animal o lote pasó enteros en una sola estadía en un corral. Lo
ambiguo se declara no calculable, igual que todo el resto del sistema.

## Decisiones

### 1. La conversión por corral se deriva en `apps.metrics`, sin modelo nuevo

`pen_conversion(*, pen, start, end)` es una función pura sobre eventos, hermana de
`pen_occupancy_report` (adr-34) y `pen_cost_summary` (adr-33). No hay tabla, no hay
migración: la conversión es una afirmación derivada, no un dato almacenado
([[adr-29-metrics-derivation]] regla 1). Una sola definición del número, la misma que
consumirán el dashboard y el asesor.

*Por qué:* tres consumidores con tres definiciones de "conversión por corral" es lo
que la doctrina de métricas existe para evitar.

### 2. Un kilo de engorde se atribuye a un corral sólo si el tramo entero se pasó ahí

Un tramo de pesaje (entre dos pesajes consecutivos de un animal o lote) se atribuye al
corral donde el target estaba **al pesaje anterior**, y **sólo si** no hubo ningún
evento de `PenPlacement` estrictamente dentro del intervalo —es decir, no cambió de
corral en el medio— y ese corral es el que se está midiendo. La ubicación se deriva de
los eventos `in`/`out` de `PenPlacement` (adr-34 decisión 1): un `in` fija el corral,
un `out` lo libera.

*Por qué:* si el animal cambió de corral entre dos pesajes, el engorde de ese tramo se
repartió entre corrales de una forma que los datos no registran. Atribuirlo entero a
uno cualquiera es exactamente el número inventado de adr-29 regla 2. Un tramo limpio se
puede afirmar; uno partido, no.

### 3. Lo no atribuible se cuenta y se reporta, no se rellena

Un tramo cuyo ADG ya es no calculable (adr-28 regla 2: mismo día, o cambió el
`head_count` del lote) se **saltea** (`segments_skipped`). Un tramo calculable que no se
puede fijar a una sola estadía en el corral —porque cambió de corral, o el target no
tiene placement que lo ubique acá— se cuenta como **no atribuido**
(`segments_unattributed`). Los kilos sólo se suman sobre los tramos **atribuidos**
(`segments_attributed`).

*Por qué:* sin esos contadores no se distingue "el corral no engordó" de "no pudimos
atribuirle el engorde". Son situaciones opuestas y la respuesta correcta a cada una es
distinta — la misma lógica que `kilos_gained` ya aplica con `segments_skipped`
(adr-29 regla 3).

### 4. Sin nada honesto que dividir, devuelve `null` con el motivo

`pen_conversion` devuelve `conversion=None` con un `not_calculable` cuando no hay tramo
atribuible (`no_attributable_growth`), cuando el engorde atribuido salió plano o
negativo (`no_weight_gain`), o cuando no hay alimento registrado al corral en el período
(`no_feed_recorded`). Nunca un cero de relleno: un cero se grafica igual que un cero
real ([[adr-29-metrics-derivation]] regla 2).

*Por qué:* una conversión inventada sobre un corral sin pesajes atribuibles se lee como
un dato de gestión y puede justificar una decisión de compra. El hueco explícito le dice
al operador qué falta medir.

### 5. No toca el ledger ni ninguna otra app

`pen_conversion` es lectura pura: no postea asiento, no muta nada, no agrega variables de
entorno ni endpoints en este cut. Se entrega como función de servicio testeada, con la
misma exposición que sus hermanas `pen_occupancy_report`/`pen_cost_summary` —service-only
hasta que exista un dashboard de corrales que las consuma, que es una adición posterior
por [[adr-07-development-flow]] y [[API]].

*Por qué:* el cobro sigue siendo exclusivamente del ledger vía `feed` (adr-25). Exponer
un endpoint para una sola de las tres métricas de corral, sin frontend que lo use, sería
asimétrico y agregaría una ruta sin consumidor.

## Consecuencias

- El backend entra por el flujo [[TDD]] (adr-07); los tests corren a nivel de servicio,
  igual que `test_placement.py`.
- `pen_closeout(*, pen, start, end)` compone la mitad de ocupación
  (`pen_occupancy_report`) con la de conversión (`pen_conversion`) en un solo cierre
  honesto por corral; cada mitad carga su propio `not_calculable`.
- La conversión **por cliente** (`conversion`, adr-29) no cambia: sigue siendo el total
  del cliente. Esta métrica es su desagregado por corral, con el hueco honesto donde la
  atribución no alcanza.
- Cualquier cambio a las reglas 1–4 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
