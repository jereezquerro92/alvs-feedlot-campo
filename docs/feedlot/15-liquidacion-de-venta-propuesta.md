# 15 · Liquidación de venta — propuesta diferida (Fase 4c)

> **No se construye ahora.** Este documento evalúa la liquidación de venta y la
> **difiere al dueño**: no es una decisión técnica, es una decisión comercial que
> reabre una regla de doctrina, y por eso no puede tomarla el agente por su cuenta.
> Queda como pedido de decisión, no como diseño cerrado.

## Por qué está diferido (no es una omisión, es una regla)

Dos ADR activos bloquean explícitamente construir esto sin una decisión del dueño:

- **[[adr-25-account-ledger]] regla 6:** *"`Exit` posts no ledger entry in the initial
  phases; sale settlement is a later addition and MUST arrive as its own ADR."* La
  liquidación tiene que **llegar como su propio ADR**, no colarse en una fase de UI.
- **[[adr-28-animal-lifecycle-and-sanitary]] decisión 3:** muertes y salidas **no tocan
  el ledger**, y el `sale_price_per_kg` de una salida es **informativo** porque *"la
  venta es del cliente, no del feedlot"*.

Construir la liquidación **invierte** esa segunda regla: haría que el feedlot registre
un ingreso por una venta que hoy la doctrina dice que es del cliente. Eso no es un
detalle de implementación — es un cambio de **modelo de negocio**. Quién vende, quién
cobra, y contra qué cuenta impacta la plata, es una definición del dueño.

## Qué significa "liquidar una venta" — las tres interpretaciones posibles

El feedlot es hotelería de hacienda de terceros **más** hacienda propia. "Liquidar la
venta" quiere decir cosas distintas según de qué hacienda hablemos, y cada una implica
un modelo de datos y un asiento distinto:

1. **Venta de hacienda del cliente (hotelería).** El animal es del cliente; el feedlot
   solo lo engordó. La venta la cobra el cliente. Acá el feedlot **no** registra un
   ingreso por la venta — a lo sumo cierra la cuenta corriente de engorde de ese animal
   (que ya está cobrada por alimento/sanidad). Esta es la lectura que la doctrina actual
   ya sostiene: `Exit` sin asiento, `sale_price_per_kg` informativo.

2. **Venta de hacienda propia del feedlot.** El animal es del propio feedlot
   (`Client(kind=own)`). Acá **sí** hay un ingreso real del feedlot al vender. Esto es lo
   más parecido a lo que un asiento de venta debería capturar — pero es una cuenta propia,
   no la de un cliente.

3. **El feedlot como comisionista / consignatario.** El feedlot vende por cuenta del
   cliente y cobra una comisión. Acá el asiento no es el precio de venta, es la
   **comisión** — un ingreso de servicio del feedlot sobre una operación del cliente.

Estas tres no son variantes de UI: son **tres modelos de negocio distintos**, cada uno
con un asiento distinto (o ninguno). Elegir sin el dueño es adivinar cuál es el negocio.

## Preguntas al dueño (lo que hay que responder antes de escribir un ADR)

1. **¿Qué hacienda se liquida por acá?** ¿Solo la propia del feedlot, solo la de
   clientes en hotelería, o ambas con tratamientos distintos?
2. **En hotelería, ¿el feedlot participa del ingreso de venta?** ¿Cobra comisión,
   cobra un cargo fijo por operación, o no toca la venta y solo cierra la cuenta de
   engorde?
3. **¿Cómo se cierra la cuenta corriente de engorde de un animal vendido?** Hoy los
   cargos de alimento/sanidad quedan en el saldo del cliente. ¿La liquidación los
   compensa contra el producido de la venta, o siguen siendo un saldo que el cliente
   paga aparte (como hasta ahora)?
4. **Si hay ingreso, ¿contra qué cuenta impacta?** ¿La del cliente (crédito que baja su
   saldo), la propia del feedlot, ambas?
5. **¿La venta de hacienda propia es un `LedgerEntry` de la cuenta `own`, o va a un
   libro/estado de resultados aparte** que el ledger actual (cuenta corriente por
   cliente) no modela?
6. **¿Qué pasa con las salidas ya cargadas?** Hoy existen `Exit` con `sale_price_per_kg`
   informativo. Si mañana se liquida, ¿se liquidan retroactivamente esas salidas, o la
   liquidación aplica solo hacia adelante?

## Camino cuando el dueño decida (no antes)

En cuanto haya respuesta, el trabajo entra por el flujo normal, sin excepción:

1. **Un ADR nuevo** (adr-43+) que fije el modelo elegido y **supersede** explícitamente
   la porción de [[adr-28-animal-lifecycle-and-sanitary]] decisión 3 que hoy dice "la
   venta es del cliente, no del feedlot", si el modelo elegido la cambia. La regla 6 de
   [[adr-25-account-ledger]] se cumple: la liquidación llega como su propio ADR.
2. Entidad/servicio nuevos (probablemente un `Settlement` o un `sale`-`LedgerEntry`
   según el modelo), **sin mutar** asientos existentes — una liquidación es un asiento
   nuevo, nunca reescribir el pasado ([[adr-25-account-ledger]] regla 1).
3. La fila en [[API]] antes del código, y el código nace por [[TDD]]
   ([[adr-03-api-and-backend]], [[adr-07-development-flow]]).

## Estado

**Diferido al dueño.** No hay código ni ADR de liquidación en esta tanda —
deliberadamente. Las otras tres cosas de la Fase 4 (imputación de pagos, cierre de
ganancia por corral, y esta) se separaron por riesgo: las dos primeras eran adiciones
que la doctrina ya habilitaba y se construyeron; esta reabre una regla de negocio y se
frena hasta que el dueño defina el modelo.
