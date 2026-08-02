---
title: adr-29-metrics-derivation
type: adr
category: backend
use_case: agregar o cambiar una métrica, graficar un número en el frontend, decidir qué devolver cuando faltan datos, leer costos o crecimiento de un cliente
created: 2026-07-21
modified: 2026-08-02
tags: [adr, feedlot, metrics, derivation, phase-3]
---

# ADR-29 — Derivación de métricas y el contrato del "no calculable"

## CONTEXT

> Cada número del negocio se define una sola vez, en el backend, como función pura sobre los eventos. Y cuando faltan los insumos la función devuelve `null` con el motivo, nunca un cero de relleno.

## ASSERTIONS

1. Las métricas se derivan en `apps.metrics`, que no tiene modelos: expone funciones puras sobre los eventos operativos. El frontend grafica lo que recibe y no calcula. Una sola definición de cada número, compartida por el dashboard, los informes y los asesores.
2. Una métrica sin insumos devuelve `null` junto a un campo `not_calculable` con la causa (`no_measured_growth`, `no_weight_gain`, `no_intake_in_period`, …). Nunca un cero, un promedio de relleno ni una estimación.
3. `kilos_gained` acumula únicamente los tramos entre pesajes cuyo GDP es calculable ([[adr-28-animal-lifecycle-and-sanitary]] regla 2), y reporta cuántos tramos se saltearon: sin ese contador no se distingue "el rodeo no engordó" de "no lo medimos".
4. `cost_breakdown` suma sólo débitos. Un pago es un crédito: no reduce el costo del período, reduce el saldo. Cuánto costó y cuánto debe son dos preguntas distintas.
5. Las inconsistencias se muestran, no se bloquean. Cargar una ración con fecha posterior a la muerte del animal está permitido —la carga tardía es la norma en el campo— y el dashboard la señala para que alguien mire.
6. Todo consumidor de métricas contempla `null`. Un frontend que asuma número siempre rompe, y es correcto que rompa en desarrollo.

## FORBIDDEN

- **NEVER** calcular una métrica en el frontend (regla 1). Una métrica es una afirmación sobre la plata y los kilos del cliente, y en el navegador no es ni auditable ni testeable.
- **NEVER** devolver cero cuando falta el insumo (regla 2). Un cero se grafica igual que un cero real y le dice al operador que ya está todo bien.
- **NEVER** estimar contra un peso teórico para tapar un hueco (reglas 2–3). El número sale plausible y falso, que es peor que no salir.
- **NEVER** restar un pago del costo (regla 4). Hace que un cliente que paga parezca más barato de alimentar.
- **NEVER** bloquear una carga por inconsistente (regla 5). El operador falsea la fecha para poder seguir trabajando y ahí el dato se pierde de verdad.

## REJECTED

- **Calcular las métricas en cada consumidor** — el dashboard, el informe y el asesor cada uno con su fórmula. Es exactamente el problema que este ADR existe para cerrar: tres definiciones de "conversión alimenticia" y ninguna correcta.
- **Materializar resúmenes diarios por cliente desde el arranque** — tablas de agregados en vez de recorrer eventos. Postergado, no descartado: con volumen real hará falta, y la interfaz de las funciones no cambia cuando pase, sólo su implementación.
- **Bloquear la carga tardía o inconsistente** — validar contra la fecha de muerte y rechazar. Perdió contra la regla 5: el dato falseado es peor que el dato incómodo.

## RELATED

### related adrs

- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — regla 2, el GDP no calculable que la regla 3 acumula
- [[docs/adrs/adr-25-account-ledger]] — los asientos que la regla 4 suma
- [[docs/adrs/adr-27-advisors-generative]] — el consumidor generativo de estos números
- [[docs/adrs/adr-42-pen-conversion-honest-cut]] — el mismo corte honesto, por corral
- [[docs/adrs/adr-39-gross-margin-and-fx]] — el margen derivado sobre estas funciones

### related files

- [[docs/FEEDLOT]] — qué significa cada número en la operación
- [[docs/FEEDLOT-DATA-MODEL]] — los eventos sobre los que se deriva
- [[docs/API]] — las rutas de métricas
