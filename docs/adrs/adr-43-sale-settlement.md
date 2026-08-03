---
title: adr-43-sale-settlement
type: adr
status: active
created: 2026-07-26
tags: [adr, feedlot, ledger, livestock, sale, settlement, phase-4c]
---

# ADR-43 — La liquidación de venta: comisión de engorde y venta propia

**Contexto:** cumple el ítem que [[adr-25-account-ledger]] regla 6 dejó explícitamente
diferido (*"`Exit` posts no ledger entry in the initial phases; sale settlement is a
later addition and MUST arrive as its own ADR"*). Es una **adición**: la regla 6 se
cumple al pie de la letra — la liquidación llega como su propio ADR y jamás muta un
asiento existente ([[adr-25-account-ledger]] regla 1). Enmienda la porción de
[[adr-28-animal-lifecycle-and-sanitary]] decisión 3 que decía "la venta es del cliente,
no del feedlot" — enmienda in-place, con consentimiento del dueño dado en conversación
([[adr-00-adr-doctrine]] regla 4b); las muertes siguen sin tocar el ledger, esa parte no
cambia. Reglas solamente; las entidades viven en [[FEEDLOT-DATA-MODEL]].

## Contexto

Una salida (`Exit`) de tipo venta cierra la vida del animal o del lote en el feedlot,
pero hasta acá no dejaba ninguna huella económica: `sale_price_per_kg` era informativo y
no posteaba nada. El dueño definió el modelo comercial que faltaba, y son **dos casos
distintos** que se diferencian por de quién es la hacienda (`Client.kind`):

- **Hacienda de cliente (`kind=boarding`).** El animal es del cliente; el feedlot solo
  lo engordó. El cliente vende y cobra la venta; el feedlot cobra una **comisión de
  engorde** — un porcentaje sobre lo que el animal engordó mientras estuvo en el feedlot.
- **Hacienda propia (`kind=own`).** El animal es del feedlot. La venta es del feedlot: el
  producido es un ingreso propio que compensa los costos ya acumulados en la cuenta propia.

Son dos asientos distintos, contra dos clases de cuenta distintas. El sistema los
diferencia por `Client.kind`, no por un campo aparte que el operador tenga que recordar.

## Decisiones

### 1. La liquidación es un asiento nuevo, nunca muta lo existente

Liquidar una venta postea **un `LedgerEntry` nuevo** en la cuenta del dueño de la
hacienda. No edita ni borra ningún asiento previo, no reabre los cargos de alimento o
sanidad ya posteados (esos quedan cobrados) y no reescribe la salida
([[adr-25-account-ledger]] regla 1, intacta). El asiento se liga a la salida por el par
genérico `(source_kind="exit", source_id=<Exit.id>)` ([[adr-24-feedlot-domain]] regla 4),
para que la liquidación sea trazable al hecho que la produjo.

*Por qué:* misma disciplina event-sourced de todo el sistema. Una liquidación es un hecho
nuevo, no una corrección del pasado.

### 2. Hacienda de cliente: comisión de engorde como DÉBITO

Una salida-venta de un animal o lote de un `Client(kind=boarding)` postea un **débito**
`concept=service` a la cuenta del cliente, por la **comisión de engorde**:

```
comisión = (engorde_commission_pct / 100) × kilos_ganados × sale_price_per_kg
```

`kilos_ganados` son los kilos que el target engordó dentro del feedlot, medidos de
pesaje a pesaje sobre los tramos medibles (el mismo corte honesto de `kilos_gained`,
[[adr-29-metrics-derivation]] regla 3, [[adr-28-animal-lifecycle-and-sanitary]] regla 2).
El asiento **fotografía** `unit_price` (= `sale_price_per_kg`) y `quantity`
(= kilos ganados) del día ([[adr-25-account-ledger]] regla 3): un cambio posterior de
precio nunca altera la comisión ya liquidada.

*Por qué:* la venta es del cliente; el feedlot no registra el precio de venta como
ingreso propio. Lo que el feedlot cobra por hotelería es el servicio de engordar, y el
dueño lo fijó como un porcentaje sobre los kilos ganados valuados al precio de venta —
no sobre el peso total, que incluye el peso de ingreso que el cliente ya traía.

### 3. Hacienda propia: el producido como CRÉDITO en la cuenta propia

Una salida-venta de un animal o lote de un `Client(kind=own)` postea un **crédito**
`concept=sale` a la cuenta propia, por el producido de la venta:

```
producido = weight × sale_price_per_kg
```

donde `weight` es el peso vendido registrado en la salida. Como la cuenta propia ya
acumula los costos de alimento y sanidad de la hacienda propia como débitos, el crédito
de venta los compensa: el saldo neto de la cuenta propia tiende al **margen** (producido
− costos). El asiento fotografía `unit_price` (= `sale_price_per_kg`) y `quantity`
(= `weight`) del día ([[adr-25-account-ledger]] regla 3).

*Por qué:* la venta de hacienda propia sí es un ingreso del feedlot. Registrarlo como
crédito en la misma cuenta que llevó los costos deja el margen legible sin inventar un
estado de resultados aparte que el ledger hoy no modela. El signo es el correcto: un
crédito baja el saldo (adr-25 regla 2, saldo positivo = se debe), y un ingreso propio
reduce lo que la cuenta propia "debe" contra sus costos.

### 4. Corte honesto: sin insumo medible, no se postea nada

La liquidación es opcional y **gateada por sus insumos**. No se postea ningún asiento
cuando:

- falta `sale_price_per_kg` (no hay precio con qué valuar), o
- en el caso boarding, falta `engorde_commission_pct` o los kilos ganados no son
  medibles / dan cero o negativo (mismo hueco que `kilos_gained`,
  [[adr-29-metrics-derivation]] regla 2), o
- en el caso propio, falta `weight`.

En esos casos la salida se registra igual que hasta ahora, sin liquidación — nunca un
cargo de relleno sobre datos que no están. Un cargo inventado sobre un lote sin pesajes
se lee como gestión real y puede justificar una decisión de plata; el hueco explícito
dice que falta medir.

*Por qué:* la doctrina de métricas prohíbe fabricar un número cuando faltan los insumos
([[adr-29-metrics-derivation]] regla 2). Un asiento fabricado es peor que una métrica
fabricada: mueve el saldo real de un cliente.

### 5. Muertes y transferencias no liquidan; solo la venta

La liquidación aplica **exclusivamente** a `Exit.kind=sale`. Una muerte (`Death`) sigue
sin tocar el ledger — esa parte de [[adr-28-animal-lifecycle-and-sanitary]] decisión 3
queda intacta. Una salida `kind=transfer` u `other` (retiro sin venta) tampoco postea:
no hubo venta que liquidar. El consumo ya cobrado no se revierte por una salida, igual
que no se revertía por una muerte.

*Por qué:* la enmienda a adr-28 decisión 3 es quirúrgica — cambia solo "la venta es del
cliente, no del feedlot" para el caso venta, y no toca la regla de que muertes y retiros
no generan asiento.

### 6. La diferenciación se deriva de `Client.kind`, no de un campo nuevo del evento

Qué asiento se postea (comisión-débito vs venta-crédito) lo decide `Client.kind` del
dueño de la hacienda, resuelto desde el `Animal`/`Lot` de la salida. La salida gana un
solo campo nuevo, `engorde_commission_pct` (nullable), que solo aplica al caso boarding;
la hacienda propia lo ignora. No se agrega un "modo de liquidación" redundante con
`kind`.

*Por qué:* `Client.kind` ya existe y ya distingue hotelería de hacienda propia. Duplicar
esa distinción en el evento invita a que los dos campos se contradigan.

## Consecuencias

- El backend entra solo por [[API]] ([[adr-03-api-and-backend]]) y nace por el flujo
  [[TDD]] ([[adr-07-development-flow]]); este ADR no exceptúa ese camino.
- Los modelos nuevos son mínimos: un campo `engorde_commission_pct` en `Exit` y un
  `Concept.SALE` en `ledger`. No hay tabla `Settlement` — la liquidación **es** un
  `LedgerEntry`, no un modelo aparte.
- `register_exit` gana la lógica de liquidación, gateada; las salidas ya cargadas sin
  liquidación siguen válidas (la liquidación aplica hacia adelante, no reprocesa el
  pasado). Reliquidar una salida vieja, si se necesita, es una acción explícita futura
  con su propio cambio.
- El saldo de un cliente boarding sube por la comisión (un cargo más de servicio); el
  saldo de la cuenta propia baja por el crédito de venta (el margen se hace legible).
- Cualquier cambio a las reglas 1–6 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
