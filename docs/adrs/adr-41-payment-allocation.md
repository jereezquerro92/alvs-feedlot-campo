---
title: adr-41-payment-allocation
type: adr
category: backend
use_case: imputar un pago contra cargos, leer el pendiente por cargo, corregir una imputación equivocada
created: 2026-07-25
modified: 2026-08-02
tags: [adr, feedlot, ledger, payment, allocation, imputation, phase-4a]
---

# ADR-41 — Imputación de pagos a cargos

## CONTEXT

> Qué cargos saldó un pago. El crédito ya movió el saldo total cuando se posteó; la imputación es una anotación aparte que clasifica ese crédito contra los débitos, sin tocar ni un asiento.

## ASSERTIONS

1. `PaymentAllocation` liga un `Payment` a un `LedgerEntry` débito con un `amount`. No es un asiento, no postea al ledger y no mueve el saldo total —ese ya se movió con el crédito del pago ([[adr-25-account-ledger]] regla 7)—. Ningún `LedgerEntry` se edita ni se borra ([[adr-25-account-ledger]] regla 1).
2. `impute_payment` rechaza en el servicio: un `entry` que no sea un débito de la misma cuenta del pago, un `amount` no positivo, una asignación que haga que lo imputado de un pago supere su monto, y una que haga que lo imputado contra un débito supere el suyo.
3. La política por defecto es FIFO: `auto_impute_payment_fifo` imputa contra los débitos pendientes del más viejo al más nuevo, hasta agotar el pago o los cargos. Una imputación explícita —una lista de `(entry, amount)`— tiene prioridad cuando el operador decide otro reparto.
4. `outstanding_charges(account)` deriva por cada débito cuánto se le imputó y cuánto queda pendiente. No se guarda un campo `paid` ni `outstanding` en `LedgerEntry`, misma disciplina que el saldo ([[adr-25-account-ledger]] regla 2).
5. `PaymentAllocation` expone `list`/`retrieve`/`create`, sin `update` ni `destroy` ([[adr-24-feedlot-domain]] regla 3). Una imputación equivocada se corrige con otra asignación, nunca editando la fila.
6. Imputar no cambia el saldo total: es clasificar un crédito ya posteado, no cobrar de nuevo. Un cliente con saldo cero y todos sus cargos imputados y otro con saldo cero y nada imputado deben exactamente lo mismo.

## FORBIDDEN

- **NEVER** bajar el `amount` de un débito al cobrarlo (regla 1). Reescribe el pasado, que es justo lo que la doctrina del ledger prohíbe.
- **NEVER** imputar entre cuentas distintas (regla 2). El pago de un cliente no salda el cargo de otro.
- **NEVER** sobre-imputar un pago ni un cargo (regla 2). Un pago no puede saldar más de lo que es, ni un cargo quedar saldado por encima de su valor.
- **NEVER** guardar un campo `paid` u `outstanding` (regla 4). Se desincroniza de las asignaciones en cuanto se agrega una.
- **NEVER** editar una asignación (regla 5). La corrección es otra asignación.

## REJECTED

- **Imputar mutando el débito** — descontar del cargo lo que se va pagando. Rechazado de plano por la regla 1: sería el ledger reescribiéndose.
- **Dejar la política por defecto sin fijar** — que cada llamador elija su orden de imputación. Rechazado por la regla 3: fijar FIFO en el ADR evita que aparezcan varias políticas implícitas y no auditables.
- **La contra-imputación explícita en este cut** — un modo de anular una asignación con un monto negativo dedicado. Postergado: esta fase entrega la imputación positiva y la corrección entra con su propio cambio.

## RELATED

### related adrs

- [[docs/adrs/adr-25-account-ledger]] — reglas 1, 2 y 7, el asiento inmutable, el saldo derivado y el pago
- [[docs/adrs/adr-24-feedlot-domain]] — regla 3, el hecho inmutable
- [[docs/adrs/adr-29-metrics-derivation]] — regla 4, por qué un pago no es un costo

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `PaymentAllocation`, `Payment`, `LedgerEntry`
- [[docs/API]] — las rutas de imputación y de pendiente por cargo
