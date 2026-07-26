---
title: adr-41-payment-allocation
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, ledger, payment, allocation, imputation, phase-4a]
---

# ADR-41 — Imputación de pagos a cargos

**Estado:** activo (Fase 4a)
**Contexto:** implementa el ítem que [[adr-25-account-ledger]] regla 7 dejó
explícitamente diferido ("Explicit payment-to-charge imputation, if needed, is a
later addition with its own model — never by mutating entries"). Es una **adición**,
no una supersesión: la regla 7 sigue siendo verdad — la imputación llega con su
propio modelo y jamás muta un asiento. Reglas solamente; las entidades viven en
[[FEEDLOT-DATA-MODEL]].

## Contexto

El ledger (adr-25) registra débitos (cargos) y créditos (pagos) y deriva el saldo
total como Σ débitos − Σ créditos. Un `Payment` postea un crédito que baja el saldo
**total**, pero hasta acá nada dice *qué cargos* saldó ese pago. La regla 7 previó
que si algún día se necesita esa imputación, entra con su propio modelo, sin tocar
los asientos. Esta fase la construye.

## Decisiones

### 1. La imputación es su propio modelo y NO toca ningún asiento

`PaymentAllocation` liga un `Payment` a un `LedgerEntry` **débito** con un `amount`.
No es un `LedgerEntry`, no postea al ledger y no mueve el saldo total — ese ya se
movió cuando el pago posteó su crédito (adr-25 regla 7). Es una anotación de
bookkeeping que dice "de este pago, tanto salda este cargo". Ningún `LedgerEntry`
se edita ni se borra jamás (adr-25 regla 1, intacta).

*Por qué:* el saldo total es una cosa (Σ débitos − Σ créditos, adr-25 regla 2) y la
imputación a cargos es otra. Mezclarlas —por ejemplo bajando el `amount` de un
débito al cobrarlo— reescribiría el pasado, exactamente lo que la doctrina del ledger
prohíbe.

### 2. La asignación se valida, nunca sobre-imputa

`impute_payment` rechaza en el **servicio**: un `entry` que no sea un débito de la
misma cuenta del pago; un `amount` no positivo; una asignación que haga que lo
imputado de un pago supere su `amount`; o que lo imputado contra un débito supere el
`amount` del débito. Un `LedgerEntry` y un `Payment` de cuentas distintas no se
imputan.

*Por qué:* un pago no puede saldar más de lo que es, ni un cargo puede quedar
saldado por encima de su valor. La validación vive en el servicio, único punto de
escritura, para que vista, admin y comando compartan la misma regla.

### 3. La política por defecto es FIFO; la explícita manda

`auto_impute_payment_fifo` imputa un pago contra los débitos pendientes de la cuenta,
del más viejo al más nuevo, hasta agotar el pago o los cargos. Es la política por
defecto y se declara acá (no queda "pendiente de confirmación" como el reparto de
alimento de adr-25 regla 5). Una imputación explícita —una lista de `(entry, amount)`—
tiene prioridad y se usa cuando el operador decide otro reparto.

*Por qué:* fijar la política por defecto en el ADR evita que cada llamador invente la
suya. FIFO es la convención contable habitual (el cargo más antiguo se salda primero)
y es auditable; la explícita cubre el caso en que el negocio quiere otra cosa.

### 4. El pendiente por cargo es una derivación, no un campo

`outstanding_charges(account)` deriva, por cada débito de la cuenta, cuánto se le
imputó (Σ `PaymentAllocation.amount`) y cuánto queda pendiente (`amount` − imputado).
No se guarda un campo `paid` ni `outstanding` en `LedgerEntry`.

*Por qué:* misma disciplina que el saldo (adr-25 regla 2): el pendiente se deriva de
los hechos, nunca se denormaliza como verdad editable. Un campo `paid` mutable se
desincronizaría de las asignaciones.

### 5. La asignación es un hecho inmutable: se crea y se lee

`PaymentAllocation` expone `list`/`retrieve`/`create` — sin `update` ni `destroy`
(adr-24 regla 3). Una imputación equivocada se corrige con otra asignación (una
contra-imputación con `amount` negativo compensa), nunca editando la fila. La
contra-imputación explícita, si se necesita, es una adición futura con su propio
cambio — esta fase entrega la imputación positiva.

*Por qué:* misma postura event-sourced del resto del sistema. Un hecho fechado no se
reescribe.

## Consecuencias

- El backend entra solo por [[API]] (adr-03) y nace por el flujo [[TDD]] (adr-07).
- `PaymentAllocation` es el único modelo nuevo; `LedgerEntry`, `Payment` y el saldo
  no se refactorizan. La imputación compone sobre el ledger, no lo reforma.
- El saldo total del cliente **no cambia** por imputar: imputar es clasificar un
  crédito ya posteado contra cargos, no cobrar de nuevo. Un cliente con saldo 0 y
  todos sus cargos imputados, y uno con saldo 0 y nada imputado, deben el mismo total.
- Cualquier cambio a las reglas 1–5 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
