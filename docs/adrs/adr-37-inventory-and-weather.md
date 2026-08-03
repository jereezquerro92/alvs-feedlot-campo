---
title: adr-37-inventory-and-weather
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, inventory, weather, stock, phase-10]
---

# ADR-37 — Inventario general de insumos y registro de clima

**Contexto:** generaliza el patrón de stock de [[adr-25-account-ledger]] regla 4
(`FeedStockMovement`) a insumos que no son alimento (gasoil, postes, alambre,
sanitarios de campo) y agrega el registro de lluvia/clima. Reusa la postura
event-sourced de [[adr-24-feedlot-domain]] regla 3 y el precedente "producción/consumo
propio no toca el ledger" de [[adr-32-multi-rubro-assets]] regla 4. Reglas solamente;
las entidades viven en [[FEEDLOT-DATA-MODEL]].

## Contexto

El feedlot mueve insumos que no son alimento —gasoil para la maquinaria, postes y
alambre para los corrales, sanitarios de campo— y hoy no tiene dónde anotarlos. Y
sostiene decisiones (siembra, pastoreo, sanidad) sobre la lluvia, que tampoco se
registra. Faltan dos hechos: **cuánto insumo hay** y **cuánto llovió**.

Copiar `FeedStockMovement` por cada insumo habría duplicado el mismo modelo — la
señal de extraer la abstracción. Se agrega una app `inventory` con el stock genérico
por movimientos, y una app `weather` con el registro de clima. Ninguna toca el
alimento existente ni el ledger.

## Decisiones

### 1. El stock de insumos es la suma de movimientos, nunca un número editable

`InputStockMovement` registra entradas y salidas fechadas de un `InputType` por
`(owner_kind, client)`. El stock actual se **deriva** — Σ entradas − Σ salidas —
exactamente como `FeedStockMovement` (adr-25 regla 4). Nunca se guarda un campo
`stock` editable en `InputType`.

*Por qué:* misma disciplina que todo el sistema. Un saldo editable pierde la
historia de por qué cambió; el movimiento la conserva y hace auditable el stock.

### 2. `InputType` es catálogo editable; el movimiento es inmutable

`InputType` (gasoil, postes, alambre, sanitario…) es dato maestro: ModelViewSet con
CRUD completo — "cargar insumos" es crear tipos. `InputStockMovement` es un hecho
fechado: list/retrieve/create, sin update ni destroy (adr-24 regla 3). Una corrección
es otro movimiento.

*Por qué:* un tipo de insumo tiene estado que se corrige (se da de baja, se renombra);
un movimiento de ayer no se reescribe.

### 3. El inventario NO toca el ledger

Ningún `InputStockMovement` postea asiento. Un insumo comprado para el feedlot es
consumo propio, no un insumo entregado a un cliente que se cobre (mismo criterio que
`Cutting`/adr-32 regla 4 y el harvest propio). El `unit_price` de una entrada es
**informativo** —permite valuar el stock— y no genera cargo.

*Por qué:* un solo camino de cobro sigue siendo el ledger vía `feed` (adr-25). Si algún
día un insumo se factura como servicio a un tercero, entra por el par genérico
`(source_kind, source_id)` (adr-24 regla 4) con su propio cambio, no por acá.

### 4. Un `InputType` inactivo rechaza movimientos nuevos, en el servicio

`register_input_movement` rechaza en el **servicio** (no en la vista) un `InputType`
con `is_active=False` y una `quantity` no positiva. La carga tardía con fecha
retroactiva se acepta. Un stock que quede negativo por carga parcial **no se bloquea**:
se muestra como inconsistencia (postura de adr-29 regla 5 — mostrar, no bloquear), no
se falsea la fecha para poder cargar.

*Por qué:* las reglas de negocio viven en el servicio, único punto de escritura, para
que vista, admin y comando compartan la misma validación.

### 5. El clima es un evento inmutable independiente del ledger y del dominio

`WeatherLog` registra por fecha la lluvia (`rainfall_mm`) y, opcional, temperatura
mín/máx y una nota, por `site`. Es un hecho fechado inmutable: list/retrieve/create.
No postea asiento, no referencia hacienda ni cuenta — es un dato ambiental que las
métricas leen, no un hecho económico.

*Por qué:* la lluvia es contexto para decidir, no una transacción. Modelarla como
evento inmutable la deja auditable y agregable sin acoplarla a ningún dominio.

## Consecuencias

- El backend entra solo por [[API]] (adr-03) y nace por el flujo [[TDD]] (adr-07).
- `apps.metrics` gana dos lecturas puras: stock actual por insumo y resumen de lluvia
  del período. No define un número nuevo del negocio, sólo agrega sobre los eventos
  nuevos (adr-29 regla 1).
- No se agregan variables de entorno: ambas apps son datos internos, sin credenciales
  ni servicios externos.
- `Animal`/`Lot` y `feed` no se refactorizan: la extracción mira hacia adelante, cubre
  los insumos nuevos, no migra el alimento que ya funciona (mismo criterio que adr-32
  regla 2).
- Cualquier cambio a las reglas 1–5 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
