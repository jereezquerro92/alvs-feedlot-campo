---
title: adr-39-gross-margin-and-fx
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, margins, fx, currency, metrics, phase-12]
---

# ADR-39 — Margen bruto derivado y tipo de cambio de referencia

**Contexto:** cierra el roadmap. Reusa las métricas de [[adr-29-metrics-derivation]]
(una sola definición de cada número), el precio de mercado de [[adr-30-market-prices-connectors]]
como valor de referencia, y no toca el ledger, que sigue en ARS con precio histórico
([[adr-25-account-ledger]] regla 3). Crece por adición ([[adr-49-domain-layer-and-growth-by-addition]]).
Reglas solamente; las entidades viven en [[FEEDLOT-DATA-MODEL]].

## Contexto

El sistema sabe cuánto costó alimentar a un cliente (`cost_breakdown`) y cuántos kilos
produjo (`kilos_gained`), pero nunca cruzó ambos en un **margen bruto**: cuánto valió lo
producido menos lo que costó. Y todo está en ARS; un cliente que razona en dólares no
tiene dónde leer una cifra de referencia en USD. Faltan dos cosas: el **margen** derivado
y un **tipo de cambio** de referencia para expresarlo en otra moneda.

## Decisiones

### 1. El tipo de cambio es una serie de referencia, no la moneda de la cuenta

`FxRate` es una fila fechada por `(currency, date, source)` con el `rate` en ARS por una
unidad de `currency` (p.ej. USD→ARS). Es un valor de referencia externo, exactamente
como el precio de mercado de hacienda (adr-30): **no** redenomina el ledger, que sigue en
ARS con precio histórico por asiento ([[adr-25-account-ledger]] regla 3).

*Por qué:* la cuenta corriente es un contrato en pesos; convertirla a dólares cambiaría
el monto que el cliente debe según el día en que se mire. El tipo de cambio expresa, no
redefine.

### 2. `FxRate` es idempotente por su tripleta y el rate es positivo

Reingerir un `(currency, date, source)` actualiza la fila, no la duplica — misma
disciplina que `MarketPrice` (adr-30 regla 6). `register_fx_rate` rechaza un `rate` no
positivo. En esta fase la carga es manual (`source="manual"`); un conector automático es
una adición futura con su propio cambio, no parte de este cut.

*Por qué:* la fuente es la verdad, la fila es cache de la última lectura. Un rate cero o
negativo no es un tipo de cambio, es un dato roto.

### 3. El margen bruto se deriva en `apps.metrics`, con una sola definición

`gross_margin` vive en `apps.metrics` (adr-29 regla 1), no en un app nuevo: es una
métrica, no un modelo. Cruza `kilos_gained` × precio de mercado de referencia (ingreso)
contra `cost_breakdown` (costo, solo débitos, adr-29 regla 4). El asesor, el dashboard y
esta cifra leen los mismos números porque son la misma fuente.

*Por qué:* tres consumidores con tres definiciones de "margen" es lo que la doctrina de
métricas existe para evitar. El único modelo nuevo es `FxRate`; el margen es función pura.

### 4. Cada insumo faltante devuelve `null` con su motivo, nunca un relleno

`gross_margin` devuelve `null` con `not_calculable` cuando falta cualquier insumo:
`no_measured_growth`/`no_weight_gain` (sin kilos medibles, adr-29 regla 2),
`no_reference_price` (sin precio de mercado para la categoría/fuente) o, al pedir otra
moneda, `no_fx_rate` (el monto en ARS sale igual; solo la conversión queda en `null`).

*Por qué:* un margen inventado sobre un lote sin pesajes se lee como gestión y justifica
una compra. El hueco explícito dice qué falta medir; el número inventado dice que ya está
todo bien.

### 5. El ingreso es de referencia, no un asiento

El "ingreso" del margen es kilos producidos × precio de mercado — un valor teórico de
gestión, no plata cobrada. No postea ningún `LedgerEntry`: la venta es del cliente, no del
feedlot ([[adr-28-animal-lifecycle-and-sanitary]] regla 3). El margen informa; el ledger
cobra, y siguen siendo cosas distintas.

*Por qué:* un solo camino de cobro sigue siendo el ledger vía `feed` (adr-25). Confundir
un margen de referencia con un ingreso real reabriría la puerta que la doctrina cerró.

## Consecuencias

- El backend entra solo por [[API]] (adr-03) y nace por el flujo [[TDD]] (adr-07).
- `FX_` no agrega credenciales: la carga de `FxRate` es manual en esta fase, sin servicio
  externo. Un conector (BCRA u otro) entra después con su propio ADR, como los de adr-30.
- `apps.metrics` gana `gross_margin`; `apps.fx` aporta el único modelo nuevo (`FxRate`) y
  sus servicios `register_fx_rate`/`latest_rate`. `market`, `ledger` y `livestock` no se
  refactorizan.
- Cualquier cambio a las reglas 1–5 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
