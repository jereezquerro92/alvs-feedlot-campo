# ADR-29 — Derivación de métricas y el contrato del "no calculable"

**Estado:** propuesto (Fase 3)
**Contexto:** consume [[adr-25-account-ledger]] y [[adr-28-animal-lifecycle-and-sanitary]]; lo consumirá [[adr-27-advisors-generative]].

## Contexto

El dashboard, los informes y los asesores de la Fase 5 necesitan los mismos
números. Si cada uno los calcula por su lado, tres consumidores terminan con tres
definiciones de "conversión alimenticia" y ninguna es la correcta.

## Decisiones

### 1. Las métricas se derivan en el backend, en una sola app

`apps.metrics` no tiene modelos: expone funciones puras sobre los eventos
operativos. El frontend grafica lo que recibe; no calcula.

*Por qué:* una métrica es una afirmación sobre la plata y los kilos del cliente.
Tiene que ser auditable, testeable y reproducible, y nada de eso se consigue en
JavaScript dentro del navegador. Además garantiza que el asesor de la Fase 5 y el
gráfico que mira el cliente digan lo mismo.

### 2. Una métrica que no se puede calcular devuelve `null` y el motivo

Ninguna función devuelve cero, un promedio de relleno ni una estimación cuando le
faltan datos. Devuelve `null` junto a un campo `not_calculable` con la causa
(`no_measured_growth`, `no_weight_gain`, `no_intake_in_period`, …).

*Por qué:* un cero se grafica igual que un cero real. Una conversión alimenticia
inventada sobre un lote sin pesajes se lee como un dato de gestión y puede
justificar una decisión de compra. El hueco explícito le dice al operador qué
tiene que ir a medir; el número inventado le dice que ya está todo bien.

### 3. El crecimiento se suma solo sobre segmentos medibles

`kilos_gained` acumula únicamente los tramos entre pesajes cuyo GDP es calculable
(adr-28 regla 2), y reporta cuántos tramos se saltearon.

*Por qué:* sin ese contador no se distingue "el rodeo no engordó" de "no lo
medimos". Son dos situaciones opuestas y la respuesta correcta a cada una es
distinta.

### 4. Los pagos no son costos

`cost_breakdown` suma solo débitos. Un pago es un crédito y no reduce el costo del
período; reduce el saldo.

*Por qué:* confundirlos hace que un cliente que paga parezca más barato de
alimentar. Son dos preguntas distintas: cuánto costó y cuánto debe.

### 5. Las inconsistencias se muestran, no se bloquean

Cargar una ración con fecha posterior a la muerte del animal está permitido: la
carga tardía de datos es la norma en el campo. El dashboard lo señala como
inconsistencia para que alguien mire.

*Por qué:* bloquear la carga obliga al operador a falsear la fecha para poder
seguir trabajando, y ahí el dato se pierde de verdad. Mejor aceptarlo y marcarlo.

## Consecuencias

- Todo consumidor de métricas debe contemplar `null`. Un frontend que asuma número
  siempre va a romper, y es correcto que rompa en desarrollo y no en producción.
- Las agregaciones recorren eventos: con volumen real habrá que materializar
  resúmenes diarios por cliente. La interfaz de las funciones no cambia cuando eso
  pase, solo su implementación.
