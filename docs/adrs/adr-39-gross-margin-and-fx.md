---
title: adr-39-gross-margin-and-fx
type: adr
category: backend
use_case: leer o cambiar el margen bruto, cargar un tipo de cambio, expresar una cifra en otra moneda
created: 2026-07-25
modified: 2026-08-02
tags: [adr, feedlot, margins, fx, currency, metrics, phase-12]
---

# ADR-39 — Margen bruto derivado y tipo de cambio de referencia

## CONTEXT

> Cruzar lo que costó contra lo que valió lo producido, y poder expresarlo en otra moneda. El margen es una función derivada y el tipo de cambio una serie de referencia: ninguno redenomina la cuenta ni postea un asiento.

## ASSERTIONS

1. `FxRate` es una fila fechada por `(currency, date, source)` con el `rate` en ARS por unidad de `currency`. Es un valor de referencia externo, como el precio de mercado ([[adr-30-market-prices-connectors]]): no redenomina el ledger, que sigue en ARS con precio histórico por asiento ([[adr-25-account-ledger]] regla 3).
2. `FxRate` es idempotente por su tripleta —reingerir actualiza la fila, no la duplica— y `register_fx_rate` rechaza un `rate` no positivo. La carga es manual (`source="manual"`); un conector automático entra con su propio cambio.
3. `gross_margin` vive en `apps.metrics` ([[adr-29-metrics-derivation]] regla 1), no en una app nueva: es una métrica, no un modelo. Cruza `kilos_gained` × precio de mercado de referencia contra `cost_breakdown`, que suma sólo débitos ([[adr-29-metrics-derivation]] regla 4).
4. `gross_margin` devuelve `null` con su `not_calculable` cuando falta cualquier insumo: `no_measured_growth` o `no_weight_gain` sin kilos medibles, `no_reference_price` sin precio para la categoría o fuente, y `no_fx_rate` al pedir otra moneda —en ese último caso el monto en ARS sale igual y sólo la conversión queda en `null`.
5. El ingreso del margen es un valor teórico de gestión —kilos producidos × precio de mercado—, no plata cobrada, y no postea ningún `LedgerEntry`. La única salida que sí liquida es la venta, y la rige [[adr-43-sale-settlement]].
6. `apps.fx` aporta el único modelo nuevo con sus servicios `register_fx_rate` y `latest_rate`; `market`, `ledger` y `livestock` no se refactorizan. No se agregan credenciales.

## FORBIDDEN

- **NEVER** redenominar la cuenta con un tipo de cambio (regla 1). La cuenta corriente es un contrato en pesos, y convertirla cambiaría lo que el cliente debe según el día en que se mire.
- **NEVER** postear un asiento por el ingreso teórico del margen (regla 5). Confundir un margen de referencia con plata cobrada reabre la puerta que la doctrina cerró.
- **NEVER** devolver un margen de relleno cuando falta un insumo (regla 4). Un margen inventado sobre un lote sin pesajes se lee como gestión y justifica una compra.
- **NEVER** guardar un `rate` cero o negativo (regla 2). No es un tipo de cambio, es un dato roto.
- **NEVER** definir el margen fuera de `apps.metrics` (regla 3). Tres consumidores con tres definiciones de "margen" es lo que la doctrina de métricas existe para evitar.

## REJECTED

- **Llevar la cuenta en moneda dual** — asientos convertidos a USD junto al monto en pesos. Rechazado por la regla 1: el saldo pasaría a depender del día en que se lo mira.
- **Un conector automático de tipo de cambio en este cut** — BCRA u otra fuente ingerida como los precios. Postergado explícitamente; entra con su propio cambio, siguiendo el patrón de [[adr-30-market-prices-connectors]].
- **Una app propia para el margen** — `margins`, con su modelo y sus filas. Rechazado por la regla 3: el margen es una función pura sobre eventos, y almacenarlo lo dejaría viejo al día siguiente.

## RELATED

### related adrs

- [[docs/adrs/adr-29-metrics-derivation]] — reglas 1, 2 y 4, dónde vive el número y qué devuelve sin insumos
- [[docs/adrs/adr-30-market-prices-connectors]] — el precio de referencia y la disciplina idempotente
- [[docs/adrs/adr-25-account-ledger]] — regla 3, la cuenta en ARS con precio histórico
- [[docs/adrs/adr-43-sale-settlement]] — la venta, que sí liquida

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `FxRate`
- [[docs/API]] — las rutas de margen y tipo de cambio
