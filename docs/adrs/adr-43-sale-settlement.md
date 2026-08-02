---
title: adr-43-sale-settlement
type: adr
category: backend
use_case: registrar una salida por venta, liquidar la comisión de engorde o el producido propio, leer el margen de la cuenta propia
created: 2026-07-26
modified: 2026-08-02
tags: [adr, feedlot, ledger, livestock, sale, settlement, phase-4c]
---

# ADR-43 — La liquidación de venta: comisión de engorde y venta propia

## CONTEXT

> Una salida por venta deja huella económica, y son dos casos distintos según de quién es la hacienda: el cliente boarding paga una comisión por el engorde, y la hacienda propia produce un ingreso del feedlot. La diferencia la decide `Client.kind`, y ninguna liquidación muta un asiento existente.

## ASSERTIONS

1. Liquidar una venta postea un `LedgerEntry` nuevo en la cuenta del dueño de la hacienda. No edita ni reabre nada: los cargos de alimento y sanidad quedan cobrados y la salida no se reescribe ([[adr-25-account-ledger]] regla 1). El asiento se liga a la salida por `(source_kind="exit", source_id=<Exit.id>)` ([[adr-24-feedlot-domain]] regla 4).
2. Hacienda de cliente (`Client.kind=boarding`): la salida-venta postea un **débito** `concept=service` por la comisión de engorde, `(engorde_commission_pct / 100) × kilos_ganados × sale_price_per_kg`. Los kilos ganados son los medidos de pesaje a pesaje sobre los tramos medibles ([[adr-29-metrics-derivation]] regla 3). El asiento fotografía `unit_price` y `quantity` del día ([[adr-25-account-ledger]] regla 3).
3. Hacienda propia (`Client.kind=own`): la salida-venta postea un **crédito** `concept=sale` por `weight × sale_price_per_kg` en la cuenta propia. Como esa cuenta ya acumula los costos como débitos, el crédito los compensa y el saldo neto tiende al margen.
4. La liquidación está gateada por sus insumos y no postea nada cuando falta `sale_price_per_kg`; cuando en el caso boarding falta `engorde_commission_pct` o los kilos ganados no son medibles, dan cero o dan negativo; o cuando en el caso propio falta `weight`. La salida se registra igual, sin liquidación.
5. La liquidación aplica exclusivamente a `Exit.kind=sale`. Una muerte sigue sin tocar el ledger y una salida `transfer` u `other` tampoco postea: no hubo venta que liquidar, y el consumo ya cobrado no se revierte.
6. Qué asiento se postea lo decide `Client.kind` del dueño, resuelto desde el `Animal` o `Lot` de la salida. El único campo nuevo es `engorde_commission_pct` (nullable), que sólo aplica al caso boarding; no hay un "modo de liquidación" redundante con `kind`.
7. No hay tabla `Settlement`: la liquidación es un `LedgerEntry`. `register_exit` gana la lógica gateada y las salidas ya cargadas siguen válidas — la liquidación aplica hacia adelante y no reprocesa el pasado.

## FORBIDDEN

- **NEVER** mutar un asiento para liquidar (regla 1). Una liquidación es un hecho nuevo, no una corrección del pasado.
- **NEVER** postear un cargo cuando falta un insumo (regla 4). Un asiento fabricado es peor que una métrica fabricada: mueve el saldo real de un cliente.
- **NEVER** cobrar la comisión sobre el peso total (regla 2). Incluiría el peso de ingreso que el cliente ya traía; lo que el feedlot cobra es el engorde.
- **NEVER** liquidar una muerte o un retiro sin venta (regla 5). No hubo venta, y revertir consumo por una salida sería otra decisión, comercial y no técnica.
- **NEVER** agregar un campo que duplique la distinción de `Client.kind` (regla 6). Dos campos que dicen lo mismo terminan contradiciéndose.

## REJECTED

- **Un modelo `Settlement` aparte** — la liquidación como su propia tabla, con su estado. Rechazado por la regla 7: la liquidación *es* un asiento, y una tabla paralela sería un segundo lugar donde mirar cuánto se cobró.
- **Registrar el precio de venta de la hacienda de cliente como ingreso propio** — tomar la venta entera del boarding. Rechazado: la venta es del cliente y el feedlot cobra el servicio de engordar, no el producido.
- **Reliquidar las salidas ya cargadas** — recorrer el pasado aplicando la nueva regla. No se hace (regla 7); si se necesita, es una acción explícita con su propio cambio.
- **`Exit` sin ninguna huella económica** — la política previa, donde `sale_price_per_kg` era informativo y ninguna salida posteaba. Reemplazada por este ADR, que [[adr-25-account-ledger]] regla 6 exigía como vehículo.

## RELATED

### related adrs

- [[docs/adrs/adr-25-account-ledger]] — reglas 1, 3 y 6, el asiento inmutable, el precio del día y el diferimiento que esto cumple
- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — la salida y la muerte, y qué parte quedó intacta
- [[docs/adrs/adr-24-feedlot-domain]] — regla 4, el par genérico que liga el asiento a la salida
- [[docs/adrs/adr-29-metrics-derivation]] — reglas 2 y 3, los kilos ganados y el hueco honesto
- [[docs/adrs/adr-47-genetics-semen-embryo]] — el mismo `Concept.SALE` en la venta de semen

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `Exit`, `LedgerEntry`, `Client`
- [[docs/feedlot/15-liquidacion-de-venta-propuesta]] — el modelo comercial que el dueño definió
- [[docs/API]] — la ruta de salidas
