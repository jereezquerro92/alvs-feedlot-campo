---
title: ADR-47 — Genética: semen, DEP y transferencia embrionaria (genetics)
type: adr
status: active
created: 2026-07-28
tags: [adr, feedlot, genetics, semen, embryo, inventory, event-sourced, phase-breeding]
---

# ADR-47 — Genética: semen, DEP y transferencia embrionaria (`genetics`)

**Contexto:** crece por adición sobre la espina ([[adr-49-domain-layer-and-growth-by-addition]] regla 1): una app
nueva `genetics`, sin tocar `livestock`. Reusa el patrón stock-por-movimientos de
[[adr-25-account-ledger]] regla 4 (`FeedStockMovement`) generalizado por
[[adr-37-inventory-and-weather]] regla 1; el precedente "la venta propia es un crédito
`concept=sale` en la cuenta propia" de [[adr-43-sale-settlement]] decisión 3; y el criterio
"producción/consumo propio no toca el ledger" de [[adr-32-multi-rubro-assets]] regla 4 y
[[adr-37-inventory-and-weather]] regla 3. La consume [[adr-46-breeding-reproduction]] (el
`Service` descuenta una pajuela o un embrión). Reglas solamente; las entidades viven en
[[FEEDLOT-DATA-MODEL]], los nombres en [[GLOSSARY]] (`GLOSSARY-feedlot-additions.md`) antes
de su primer uso ([[adr-01-glossary-and-localization]]).

## Contexto

Un rodeo de cría maneja **genética** como un activo de primera clase: toros
(reproductores) propios o externos, pajuelas de semen guardadas en termos, sus DEP/EPD
(diferencias esperadas de progenie), y la transferencia embrionaria con donantes y
receptoras. Hoy el sistema no sabe qué semen hay, de qué toro, cuántas pajuelas quedan, ni
registra una venta de semen —que el dueño definió como un **ingreso propio**—. Se agrega la
app `genetics` con el catálogo genético, el inventario de pajuelas y embriones por
movimientos, y la venta de semen, sin tocar el dominio estable.

## Decisiones

### 1. `genetics` separa catálogos editables de movimientos inmutables

Catálogos (datos maestros, ModelViewSet con CRUD completo): `Sire` (reproductor),
`SemenBatch` (partida de pajuelas), `EmbryoBatch` (partida de embriones) y `BreedingValue`
(un DEP/EPD). Hechos fechados inmutables (`list`/`retrieve`/`create`, sin `update` ni
`destroy`, [[adr-49-domain-layer-and-growth-by-addition]] regla 3): `SemenMovement`, `EmbryoMovement`,
`EmbryoFlush` (colecta) y `SemenSale` (venta).

*Por qué:* un toro o una partida tienen estado que se corrige (se da de baja, se renombra);
un movimiento de stock o una venta de ayer no se reescriben. Misma frontera catálogo/evento
del resto del sistema ([[adr-37-inventory-and-weather]] regla 2).

### 2. El stock de pajuelas y de embriones es Σ entradas − Σ salidas, nunca un campo editable

El stock de un `SemenBatch` se **deriva** de sus `SemenMovement` (`in`/`out`), y el de un
`EmbryoBatch` de sus `EmbryoMovement` —exactamente como `FeedStockMovement`
([[adr-25-account-ledger]] regla 4) e `InputStockMovement` ([[adr-37-inventory-and-weather]]
regla 1). Nunca se guarda un campo `straws_remaining` editable en la partida.

*Por qué:* misma disciplina que todo el sistema. Un saldo editable pierde la historia de por
qué cambió; el movimiento la conserva y hace auditable el stock de un termo.

### 3. Un `Sire` liga a un `Animal` propio o es externo; los DEP son catálogo, no derivados

`Sire` referencia opcionalmente un `Animal` propio (`category=bull`) o representa un toro
**externo** cuyo semen se compra sin poseer el animal (`registry_id`, `breed`). Es catálogo
editable. Un `BreedingValue` es un DEP/EPD por toro: `(trait, value, accuracy, source,
date)` —`trait` ∈ {`birth_weight`, `weaning_weight`, `milk`, `ribeye_area`, `marbling`,
`scrotal`, `other`}—; es un dato de catálogo que se carga, no una métrica derivada de los
eventos del sistema.

*Por qué:* los DEP los publica la evaluación genética (la cabaña, la raza, un servicio
externo), no se calculan de los pesajes propios; modelarlos como catálogo editable es lo
correcto. Un `Sire` externo cubre el caso real de comprar semen de un toro que no es tuyo.

### 4. La venta de semen es un ingreso propio: crédito `sale` a la cuenta propia

`SemenSale` postea **un `credit` `concept=sale`** a la cuenta propia (el `Client(kind=own)`)
por el producido de la venta, vía el par genérico `(source_kind="semen_sale",
source_id=<SemenSale.id>)` ([[adr-49-domain-layer-and-growth-by-addition]] regla 4), y descuenta un
`SemenMovement` `out` (`reason=sale`) del `SemenBatch`. Es el mismo precedente que la venta
de hacienda propia ([[adr-43-sale-settlement]] decisión 3): un producido propio se registra
como crédito en la cuenta que lleva sus costos, dejando el margen legible. Fotografía
`unit_price` × `straws` del día ([[adr-25-account-ledger]] regla 3). El comprador es
informativo (`buyer_name`, opcional `buyer_client`).

*Por qué:* el dueño definió la venta de semen como ingreso del feedlot. Registrarla como
crédito en la cuenta propia —igual que la venta de hacienda propia— la hace comparable
contra los costos genéticos sin inventar un estado de resultados aparte que el ledger no
modela. Cobrar además a un cliente comprador es una adición futura por el mismo seam, no
parte de este cut.

### 5. La transferencia embrionaria: la colecta produce inventario; el transfer lo consume en `breeding`

`EmbryoFlush` (colecta sobre una donante `Animal`) registra los embriones obtenidos con su
donante, su toro y su grado, y produce inventario: crea/actualiza un `EmbryoBatch` y postea
un `EmbryoMovement` `in`. El **transfer** a una receptora **no** vive acá: es un `Service`
con `method=embryo_transfer` en `breeding` ([[adr-46-breeding-reproduction]] decisión 7) que
descuenta un `EmbryoMovement` `out`. `genetics` lleva el inventario; `breeding` el evento
reproductivo sobre la receptora.

*Por qué:* la colecta es un hecho de producción de inventario (como una compra de pajuelas);
el transfer es un hecho reproductivo sobre un animal, que pertenece a los eventos de
`breeding` junto al servicio y la parición. Cada hecho vive en su dominio y el inventario no
se duplica.

### 6. Ni el inventario ni la colecta tocan el ledger; solo la venta postea

Ningún `SemenMovement`, `EmbryoMovement` ni `EmbryoFlush` postea un asiento —producción y
consumo propios no son insumos entregados a un cliente ([[adr-32-multi-rubro-assets]] regla
4, [[adr-37-inventory-and-weather]] regla 3). El `unit_cost` de una compra de pajuelas es
**informativo** (valúa el stock), no genera cargo. El único asiento de la app es el crédito
de venta (decisión 4). El consumo por inseminación es un `out` de stock, sin asiento; su
eventual facturación al cliente boarding la decide `breeding` como un débito de servicio
([[adr-46-breeding-reproduction]] decisión 6), no `genetics`.

*Por qué:* un solo camino de cobro. El semen consumido en una IA propia es costo interno ya
valuado por el stock; el semen vendido es el único hecho económico que sale de `genetics`.

### 7. Todo movimiento y venta valida en el servicio, no en la vista

`register_semen_movement` rechaza un `SemenBatch` inactivo y una `quantity` no positiva;
`register_semen_sale` rechaza stock insuficiente, un precio no positivo y arma el crédito y
el `out` en una transacción; `register_embryo_flush` y `register_embryo_movement` validan
igual sobre embriones. Un stock que quede negativo por carga parcial se **muestra** como
inconsistencia, no se bloquea ([[adr-37-inventory-and-weather]] regla 4,
[[adr-29-metrics-derivation]] regla 5). La carga tardía con fecha retroactiva se acepta.

*Por qué:* las reglas de negocio viven en el servicio, único punto de escritura, para que
vista, admin y comando compartan la misma validación.

### 8. Las métricas de genética se derivan en `apps.metrics`, honestas con el hueco

`apps.metrics` gana funciones puras sobre los movimientos ([[adr-29-metrics-derivation]]
regla 1): stock de pajuelas por partida y por toro, semen disponible total, y uso por toro
en el período. Sin movimientos, devuelven `null` con su `not_calculable`, nunca un cero de
relleno ([[adr-29-metrics-derivation]] regla 2).

*Por qué:* "0 pajuelas" y "nunca se cargó semen de este toro" son situaciones opuestas; el
hueco explícito las distingue.

### 9. `choices` en inglés; el español vive solo en el render

`method`, `reason`, `trait`, `grade`, `direction` y demás enums son inglés
([[adr-01-glossary-and-localization]], [[LOCALIZATION]]); las etiquetas en español existen
solo en la salida renderizada del frontend.

## Consecuencias

- El backend entra solo por [[API]] ([[adr-03-api-and-backend]]) y nace por el flujo [[TDD]]
  ([[adr-07-development-flow]]); este ADR no exceptúa ese camino
  ([[adr-49-domain-layer-and-growth-by-addition]] regla 6).
- Migraciones: las tablas nuevas viven en `genetics` (`Sire`, `BreedingValue`, `SemenBatch`,
  `SemenMovement`, `SemenSale`, `EmbryoBatch`, `EmbryoMovement`, `EmbryoFlush`). Nada fuera
  de la app; el crédito de venta reusa `Concept.SALE` ([[adr-43-sale-settlement]]) por el
  seam, sin concepto ni modelo nuevo en `ledger`.
- `Sire.animal` referencia al `Animal` existente sin agregarle un campo —la extracción mira
  hacia adelante ([[adr-32-multi-rubro-assets]] regla 2,
  [[adr-38-senasa-traceability]] precedente de la caravana).
- No se agregan variables de entorno: `genetics` es dato interno, sin credenciales ni
  servicios externos.
- El gateo RBAC de estas rutas se declara en [[API]] con su clase de permiso antes del
  código ([[adr-44-field-operational-roles]] decisión 7).
- Cualquier cambio a las reglas 1–9 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
