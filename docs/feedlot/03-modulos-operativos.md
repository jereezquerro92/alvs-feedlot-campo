# 03 · Módulos operativos y reglas de negocio

Cómo se opera cada módulo y —lo más importante— las reglas finas que definen cuándo algo cuesta, a quién y por cuánto.

## 1. Clientes y hacienda

Un **cliente** es el dueño de la hacienda. Puede ser de hotelería (un tercero al que le facturamos) o el propio feedlot (para costear la hacienda propia como centro de costo interno). Cada cliente tiene una **cuenta corriente** desde su creación.

La hacienda de un cliente se ingresa con un **evento de ingreso** que admite dos modos, porque así se trabaja en la realidad:

- **Individual (1×1):** se cargan animales uno por uno con su caravana. Sirve cuando importa el seguimiento por cabeza (reproductores, animales de valor, trazabilidad fina).
- **Por lote:** se carga "este lote: 46 vacas × N kg totales". No se individualiza; se maneja por cabezas y kilos totales. Es lo habitual para engorde masivo.

Un lote puede después "nominarse" (asociarle animales individuales) si hiciera falta, pero por defecto un lote anónimo vive con `head_count` + `total_weight` y nada más.

## 2. Alimentación y stock

### Catálogo y stock

Los **tipos de alimento** (maíz, silaje, balanceado, etc.) son un catálogo. El **stock** existe en dos titularidades:

- **Stock propio** del feedlot (lo que compramos nosotros).
- **Stock por cliente**: lo que **el cliente nos entregó** para engordar su hacienda (una `FeedDelivery` suma a su stock).

El stock se lleva como movimientos (entradas y salidas); el disponible se calcula sumando. Nunca se "pisa" un número de stock a mano.

### Carga de una ración (la regla clave)

Al cargar el alimento dado en el día se elige: cliente/objetivo, tipo de alimento, kilos, y **el origen**:

```
¿De dónde sale este alimento?
  ├─ Stock del cliente  → si tiene stock disponible, se usa ese
  └─ Stock propio       → sale del feedlot
```

De esa elección depende el costeo:

| Origen | Efecto en stock | Efecto en cuenta corriente | Cuenta para métricas |
|---|---|---|---|
| **Stock del cliente** | descuenta stock del cliente | **No genera cargo** (el cliente ya aportó ese alimento) | **Sí**, valorizado al precio del día |
| **Stock propio** | descuenta stock propio | **Genera débito** en ARS = kg × precio del día | **Sí**, valorizado al precio del día |

Esta es la regla que pediste: *"si es del cliente y en su stock tiene, se usa ese"*, y a la vez *"el dashboard muestra el costeo diario de alimentación indistintamente si el alimento es nuestro o lo aportó el cliente"*. Se logra separando dos cosas: **facturación** (solo el alimento propio se cobra) y **métrica de consumo** (todo se valoriza para saber cuánto come el lote por día).

> **[DECISIÓN 1] — Alimento propio: ¿a costo o con margen?**
> Por defecto se cobra a **precio del momento** (el `unit_price` que cargues). Si querés aplicar un margen automático (p. ej. costo × 1,15), lo agregamos como parámetro por cliente o global. A confirmar.

> **[DECISIÓN 2] — Cliente sin stock suficiente.**
> Si el cliente eligió "stock del cliente" pero no le alcanza, propongo: se sirve lo disponible desde su stock (sin cargo) y **el excedente se sirve de stock propio y se cobra**. La ración quedaría partida en dos movimientos. Alternativa: bloquear y avisar. A confirmar.

> **[DECISIÓN 3] — Precio de referencia automático.**
> El `unit_price` puede pre-cargarse desde el último precio conocido del `FeedType` y quedar editable. A confirmar si querés un historial de precios de alimento aparte.

## 3. Pesajes y crecimiento

Un **pesaje** registra el peso de un animal o los kilos totales de un lote en una fecha. De la secuencia de pesajes se derivan:

- **Ganancia diaria de peso (GDP / ADG):** (peso actual − peso anterior) / días transcurridos.
- **Peso promedio del lote:** kilos totales / cabezas.
- **Conversión alimenticia:** kg de alimento consumido / kg ganado en el mismo período. Es el cruce estrella entre el módulo de alimentación y el de pesaje (ver [dashboard](feedlot/04-dashboard-metricas.md)).

## 4. Muertes y salidas

- **Muerte / baja:** marca un animal como `dead`, o descuenta cabezas y kilos de un lote (baja parcial). Registra causa y fecha. No genera movimiento en la cuenta, pero sí impacta las métricas de mortandad y el stock de hacienda.
- **Salida / egreso:** marca un animal como vendido/egresado, o descuenta parte de un lote (cabezas + kg). Puede registrar destino y precio de venta. **[DECISIÓN 4]:** si la venta se liquida por el sistema, el egreso podría generar un movimiento (crédito por venta o cierre de costeo). Por defecto el egreso es solo trazabilidad de hacienda; la liquidación de venta queda para una fase posterior.

## 5. Sanidad

Se aplican **vacunas y tratamientos** a animales (vacas y toros) o lotes, desde un catálogo con precio. Cada aplicación registra producto, dosis, precio del momento y costo, y **genera un débito** en la cuenta del cliente (es insumo/servicio del feedlot). Mismo criterio de precio histórico que la alimentación.

## 6. Cuenta corriente y pagos

La cuenta corriente es un **libro de movimientos inmutable** (`LedgerEntry`). Cada movimiento es un débito (cargo) o un crédito (pago o ajuste a favor), en pesos, con la fecha y una referencia al evento que lo originó.

Qué genera un movimiento:

| Evento | Movimiento |
|---|---|
| Ración con alimento **propio** | débito (kg × precio del día) |
| Ración con alimento **del cliente** | — (solo baja de stock) |
| Sanidad (vacuna/tratamiento) | débito |
| Servicio manual / ajuste | débito o crédito según corresponda |
| **Pago** del cliente | crédito |

Reglas del libro:

- **Signo:** saldo positivo = el cliente **debe** (Σ débitos − Σ créditos). El saldo se muestra denormalizado para lectura rápida, pero la verdad siempre es la suma de los movimientos.
- **Inmutabilidad:** un movimiento no se edita ni se borra. ¿Te equivocaste en una carga? Se hace un **contra-asiento** (un movimiento inverso) y, si corresponde, el correcto. Así la cuenta es auditable y nunca "cambia el pasado".
- **Precio histórico:** cada débito guarda el precio unitario y la cantidad de ese día. La suba posterior de precios no altera lo ya cargado.
- **Pagos:** un pago compensa el saldo generando un crédito. No se "aplica" contra un cargo puntual (no hay imputación pago-a-factura en Fase 1); simplemente reduce el saldo total. **[DECISIÓN 5]:** si querés imputación explícita (este pago cancela estas raciones), lo modelamos aparte más adelante.

Detalle formal de estas reglas (inmutabilidad, signo, costeo genérico) en el **ADR-25 — Account & Ledger**.

## Trazabilidad de punta a punta

Como cada `LedgerEntry` guarda la referencia a su evento origen (`source_kind` + `source_id`), desde cualquier cargo de la cuenta se puede llegar al hecho que lo generó: qué ración, qué día, qué alimento, qué precio, sobre qué lote. Y al revés: desde un lote se puede reconstruir todo lo que se le dio y cuánto costó. Esa es la trazabilidad que persigue el sistema.
