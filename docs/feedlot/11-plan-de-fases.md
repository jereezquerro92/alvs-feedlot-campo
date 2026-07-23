# 11 · Plan de fases — diseño detallado

> Complementa el roadmap de [07 · Arquitectura escalable y roadmap](07-arquitectura-escalable-y-roadmap.md), que define **qué** entra en cada fase. Este documento define **cómo**: entidades exactas, servicios, endpoints, reglas y criterios de aceptación, al nivel necesario para escribir el código.

**Estado:** Fase 1 en `main` (commit `d3e5aa9`). Fase 2 en diseño.

---

## Convenciones que aplican a todas las fases

Son las que ya quedaron establecidas en la Fase 1 y no se rediscuten en cada una:

- **Eventos inmutables.** Ningún hecho operativo se edita ni se borra. Una corrección es un evento nuevo (contra-asiento en el ledger, evento de ajuste en stock).
- **Estados derivados.** Saldos de cuenta, saldos de stock, peso actual y cabezas de un lote se calculan desde los eventos. Los campos denormalizados (`balance_cached`, `current_weight`, `head_count`) son cache de lectura, nunca fuente de verdad.
- **Costeo genérico.** Cualquier evento que deba cobrarse postea al ledger con el par (`source_kind`, `source_id`). El ledger no conoce a los rubros.
- **Precio histórico.** Todo cargo captura el `unit_price` del momento. Cambiar un precio de catálogo no reescribe la historia.
- **Un servicio por regla de negocio.** La lógica vive en `services.py`, no en los viewsets ni en los modelos. Los tests apuntan al servicio.
- **Target animal-XOR-lote.** Los eventos que aplican a hacienda usan dos FK nulables (`animal`, `lot`) con restricción de base que exige exactamente una. Fundamento en ADR-26.

---

## Fase 2 — Ciclo del animal

**Objetivo:** cerrar la trazabilidad del animal desde que entra hasta que sale, y que todos los cargos sanitarios entren solos a la cuenta.

**Rama:** `feat/feedlot-phase2`.

### 2.1 · Pesajes y crecimiento (`livestock`)

**Entidad `Weighing`**

| Campo | Tipo | Notas |
|---|---|---|
| `animal` / `lot` | FK nulable | exactamente una (restricción) |
| `date` | date | |
| `weight` | decimal | kg del animal, o **kg totales** del lote |
| `head_count` | int nulable | solo modo lote: cabezas pesadas, para validar contra `Lot.head_count` |
| `method` | choice | `scale` (báscula) \| `estimated` (visual) |
| `notes` | text | |

**Servicio `register_weighing`**

1. Valida que el target esté `active`.
2. Valida que `date` no sea anterior al ingreso del target.
3. Crea el `Weighing`.
4. Actualiza el denormalizado: `Animal.current_weight`, o `Lot.total_weight`.

**Cálculo de GDP (ganancia diaria de peso / ADG)**

No es una entidad, es una **consulta derivada**. Entre dos pesajes consecutivos del mismo target:

```
GDP = (peso_final − peso_inicial) / días_transcurridos
```

Para lotes anónimos, el peso que se compara es el **promedio por cabeza** (`total_weight / head_count`), no el total — si no, un ingreso o una muerte en el medio ensucia el número. Esto importa: es la diferencia entre un GDP que sirve y uno que miente.

**[DECISIÓN]** Cuando un lote recibe hacienda nueva entre dos pesajes, el promedio por cabeza se contamina igual (entran animales con otro peso). Dos opciones: (a) invalidar el GDP del período y marcarlo como no calculable, (b) calcularlo contra el peso teórico esperado. Propongo (a) — es honesto y simple; un número ausente es mejor que uno inventado.

### 2.2 · Muertes (`livestock`)

**Entidad `Death`**

| Campo | Tipo | Notas |
|---|---|---|
| `animal` / `lot` | FK nulable | exactamente una |
| `date` | date | |
| `cause` | choice | `disease`, `accident`, `unknown`, `other` |
| `cause_detail` | text | |
| `head_count` | int nulable | solo lote: baja parcial |
| `weight` | decimal nulable | kg dados de baja (lote) |

**Servicio `register_death`**

1. Valida target activo y, en lote, que `head_count` no exceda las cabezas vivas.
2. Crea el `Death`.
3. Efecto: `Animal.status = dead`, o resta cabezas y kg al `Lot`.
4. **Sin efecto en el ledger.** Una muerte no genera cargo ni crédito.

Lo que sí cambia: a partir de esa fecha el animal ya no debería recibir raciones. El sistema **no lo impide** (puede haber carga tardía de datos con fecha anterior), pero el dashboard lo marca como inconsistencia.

**[DECISIÓN]** ¿La mortandad del período se descuenta de algún modo del costo del cliente, o el cliente paga íntegro lo que el animal consumió antes de morir? Por defecto: **paga íntegro** — el alimento se consumió realmente. Confirmar.

### 2.3 · Salidas (`livestock`)

**Entidad `Exit`**

| Campo | Tipo | Notas |
|---|---|---|
| `animal` / `lot` | FK nulable | exactamente una |
| `date` | date | |
| `kind` | choice | `sale` (venta) \| `transfer` (retiro del cliente) \| `other` |
| `destination` | char | frigorífico, campo, comprador |
| `head_count` | int nulable | solo lote: egreso parcial |
| `weight` | decimal nulable | kg de salida |
| `sale_price_per_kg` | decimal nulable | precio de venta, informativo |

**Servicio `register_exit`**

1. Valida target activo y cabezas disponibles.
2. Crea el `Exit`.
3. Efecto: `Animal.status = sold` (si `kind=sale`) o `exited`; o resta cabezas/kg al `Lot`. Si el lote queda en cero cabezas → `status = closed`.
4. **Sin efecto automático en el ledger.** La venta es del cliente, no del feedlot; el precio queda como dato informativo para métricas.

**[DECISIÓN]** Cuando sale el último animal de un cliente, ¿el sistema hace algo con el saldo de la cuenta (cierre, aviso, liquidación)? Propongo: **solo un aviso** en el dashboard ("cliente sin hacienda activa y con saldo deudor de $X"). El cierre contable es una decisión humana.

### 2.4 · Sanidad (`sanitary`)

> **Nota de nombre:** la documentación previa llamaba a esta app `health`, pero el template ya tiene un app `health` para el liveness probe (`/api/health/`). Esta app se llama **`sanitary`**. Los documentos 02 y 07 quedan desactualizados en ese punto.

**Entidad `HealthProduct`** (catálogo, editable)

`name`, `kind` (`vaccine` | `treatment` | `antiparasitic` | `other`), `unit` (dosis, ml, cc), `unit_price`, `is_active`.

**Entidad `HealthEvent`** (aplicación, inmutable)

| Campo | Tipo | Notas |
|---|---|---|
| `client` | FK | |
| `animal` / `lot` | FK nulable | exactamente una |
| `product` | FK | |
| `quantity` | decimal | dosis o unidades aplicadas |
| `head_count` | int nulable | lote: a cuántas cabezas se aplicó |
| `unit_price` | decimal | **snapshot** del precio al momento |
| `date` | date | |
| `applied_by` | char | quién aplicó |

**Servicio `register_health_event`**

1. Valida target activo y pertenencia al cliente.
2. Captura `unit_price` desde el catálogo **en el momento de la creación**.
3. Crea el `HealthEvent`.
4. Postea al ledger: **siempre débito**, por `quantity × unit_price`, con `concept='health'` y `source_kind='health_event'`.

La diferencia con alimentación: la sanidad **siempre la pone el feedlot**, así que siempre se cobra. No existe el equivalente a "producto sanitario aportado por el cliente".

**[DECISIÓN]** ¿Se lleva stock de productos sanitarios como se lleva de alimento? Propongo **que no en esta fase** — el volumen es chico y el control de vencimientos es otro problema. Si más adelante hace falta, se suma un `HealthStockMovement` reusando el patrón de `feed`.

### 2.5 · Endpoints nuevos

```
GET/POST  /api/weighings/
GET       /api/weighings/{id}/
GET       /api/animals/{id}/growth/      → serie de pesajes + GDP por período
GET       /api/lots/{id}/growth/         → idem, sobre promedio por cabeza

GET/POST  /api/deaths/
GET/POST  /api/exits/

GET/POST  /api/health-products/
GET/POST  /api/health-events/
```

Cada uno entra por `docs/API.md` según el flujo del repo.

### 2.6 · Criterios de aceptación (los tests que hay que escribir)

**Pesajes**

- Un pesaje sobre animal actualiza `current_weight`.
- Un pesaje sobre lote actualiza `total_weight`.
- Pesaje sobre target `dead` o `sold` → error.
- Pesaje con fecha anterior al ingreso → error.
- GDP entre dos pesajes de un animal da el valor esperado.
- GDP de lote se calcula sobre promedio por cabeza, no sobre total.
- GDP de un período con ingreso intermedio → no calculable.

**Muertes**

- Muerte de animal → `status = dead`.
- Muerte parcial de lote → resta cabezas y kg.
- Muerte de más cabezas que las vivas → error.
- Muerte **no** genera asiento en el ledger.

**Salidas**

- Salida de animal → `status = sold` o `exited` según `kind`.
- Salida parcial de lote → resta cabezas.
- Salida total de lote → `status = closed`.
- Salida no genera asiento en el ledger.

**Sanidad**

- Aplicación genera débito por `quantity × unit_price`.
- El `unit_price` queda congelado: cambiar el catálogo después no altera el asiento.
- Aplicación sobre target de otro cliente → error.
- El saldo de la cuenta refleja la suma de sanidad + alimentación.

### 2.7 · Orden de construcción sugerido

Cuatro commits, cada uno verde antes del siguiente:

1. `Weighing` + servicio + GDP + tests.
2. `Death` + `Exit` + servicios + tests.
3. `sanitary` completa (catálogo + evento + costeo) + tests.
4. Serializers, viewsets, URLs, admin y filas de `API.md`.

---

## Fase 3 — Dashboard y métricas

**Objetivo:** que el cliente y el operador lean la situación de un vistazo.

Es la primera fase con peso en el **frontend** (Astro + Svelte). El backend aporta endpoints de agregación; no se calcula nada en el navegador que deba ser auditable.

**Endpoints de agregación** (todos por cliente y rango de fechas):

```
GET /api/clients/{id}/metrics/summary/      → cabezas, kg totales, saldo, costo del período
GET /api/clients/{id}/metrics/daily-cost/   → serie de costo diario, desglosado por concepto
GET /api/clients/{id}/metrics/growth/       → curva de peso promedio y GDP
GET /api/clients/{id}/metrics/conversion/   → kg de alimento / kg ganado
GET /api/clients/{id}/metrics/mortality/    → cabezas muertas / cabezas ingresadas
GET /api/clients/{id}/metrics/account/      → evolución del saldo
```

**La métrica que importa:** la **conversión alimenticia** (kg consumidos ÷ kg ganados en el mismo período) es el cruce entre `feed` y `livestock` y el número que justifica el sistema entero. Requiere que ambas series existan con fechas confiables — por eso va después de la Fase 2, no antes.

**Riesgo a vigilar:** estas agregaciones sobre eventos crecen mal. Con volumen real habrá que materializar resúmenes diarios por cliente. No se optimiza ahora, pero se mide desde el principio.

**[DECISIÓN]** Biblioteca de gráficos del frontend. Sigue abierta.

---

## Fase 4 — Precios de hacienda (`market`)

**Objetivo:** referencia de mercado para métricas y para el asesor financiero. **No** afecta la cuenta corriente.

Tres modos de ingesta, en orden de confiabilidad:

1. **API abierta** (CKAN de datos.gob.ar) — automatizable, estable, es el camino preferido.
2. **Scraping** (Cañuelas / MAG) — automatizable pero frágil; se rompe cuando cambia el HTML. Necesita alerta cuando la ingesta falla o devuelve valores absurdos.
3. **Carga manual** — siempre disponible como respaldo. La fuente `manual` es un `MarketSource` más.

Detalle de fuentes en [06 · Precios de hacienda](06-precios-hacienda.md).

**Diseño:** un job programado por fuente, idempotente por (`source`, `category`, `date`). El campo `raw` guarda el payload original para poder rehacer el parseo sin volver a pedir el dato.

---

## Fase 5 — Asesores IA (`advisors`)

**Objetivo:** convertir los datos del cliente en recomendaciones legibles.

Tres asesores (ganadero, contable-financiero, administrativo), detallados en [05 · Asesores IA](05-asesores-ia.md).

**El principio no negociable:** el asesor **no consulta la base directamente**. Recibe un `input_snapshot` — un paquete de métricas ya calculadas por los endpoints de la Fase 3 — y produce un `output`. Ambos quedan guardados en `AdvisorReport`. Esto hace que cada informe sea **reproducible y auditable**: se puede mirar exactamente qué datos vio el modelo cuando dijo lo que dijo.

Depende de la Fase 3: sin métricas, no hay snapshot.

**Cuidado a tener presente:** un asesor que sugiere decisiones económicas sobre hacienda ajena tiene que ser explícito sobre su margen de error. Las recomendaciones se presentan como sugerencias con los datos que las respaldan a la vista, nunca como certezas.

---

## Fase 6+ — Multi-rubro

Se dispara recién cuando aparece el **segundo rubro real**, no antes. En ese momento se extraen a una app compartida `assets` los conceptos genéricos que ya se repitieron: `Asset`, `Task`, `MaintenanceEvent`.

Extraerlos antes de tener dos casos concretos es adivinar. El costo de esperar es bajo (una refactorización acotada); el costo de equivocarse en la abstracción es alto.

Orden tentativo por afinidad con lo ya construido: caballos (`equines`, muy parecido a `livestock`) → alfalfa y pivotes (`crops`) → maquinaria y taller (`machinery`, `workshop`).

---

## Decisiones abiertas que bloquean la Fase 2

Estas tres conviene cerrarlas antes de escribir código, porque cambian el diseño:

1. **Mortandad y costo:** ¿el cliente paga íntegro lo consumido por un animal que murió? *(propuesta: sí)*
2. **GDP con ingreso intermedio:** ¿se marca como no calculable o se estima? *(propuesta: no calculable)*
3. **Stock de sanidad:** ¿se lleva en esta fase? *(propuesta: no)*

Las demás decisiones abiertas del proyecto siguen listadas en [README](README.md).

---

## Estado de implementación

- **Fase 1** — en `main` (commit d3e5aa9).
- **Fase 2** — en `main` (ciclo del animal + `sanitary`).
- **Fase 3** — en `main` (métricas derivadas, `metrics`).
- **Fase 4** — app `market` construida (conector Cañuelas completo + framework + carga manual + comando de ingesta). Dos puntos de integración quedan para validar contra el sitio vivo desde Claude Code: el formulario de fechas de Cañuelas y el endpoint AJAX de IPCVA. Ver ADR-30.
- **Fase 5** — app `advisors` construida (snapshot sobre métricas, 3 asesores sembrados, cliente de inferencia real+mock calcado del router, reportes auditables). Punto de integración para Claude Code: cablear `AdvisorBedrockClient` contra AWS (modelo, IAM, async). Ver ADR-31.
