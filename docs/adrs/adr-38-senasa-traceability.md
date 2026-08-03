---
title: adr-38-senasa-traceability
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, traceability, senasa, renspa, dte, caravana, phase-11]
---

# ADR-38 — Trazabilidad SENASA: RENSPA, DT-e y caravana

**Contexto:** crece por adición ([[adr-49-domain-layer-and-growth-by-addition]]): una app nueva
`traceability` sobre la espina, sin tocar `livestock` ni el ledger. Reusa la postura
event-sourced de [[adr-49-domain-layer-and-growth-by-addition]] regla 3 y el precedente "un catálogo se
edita, un evento es inmutable" de [[adr-33-feedyard-operating-loop]] decisión 5.
Reglas solamente; las entidades viven en [[FEEDLOT-DATA-MODEL]].

## Contexto

El movimiento de hacienda en Argentina se documenta ante SENASA: cada
establecimiento tiene un **RENSPA**, cada traslado de animales viaja con un **DT-e**
(Documento de Tránsito electrónico) que liga un RENSPA de origen a uno de destino, y
cada animal lleva su **caravana** oficial de identificación individual. Hoy el sistema
sabe qué come y cuánto pesa un animal, pero no de dónde vino ni con qué documento —
no hay trazabilidad sanitaria. Se agrega la app `traceability` con esos tres hechos.

## Decisiones

### 1. El RENSPA es un catálogo editable; el DT-e y la caravana son inmutables

`Establishment` (un establecimiento con su `renspa`) es dato maestro: ModelViewSet con
CRUD completo — "cargar establecimientos" es crear filas. `TransitDocument` (el DT-e) y
`Caravana` son hechos fechados: list/retrieve/create, sin update ni destroy (adr-49
regla 3). Una corrección de un DT-e o una re-identificación es un registro nuevo.

*Por qué:* un establecimiento tiene estado que se corrige (se da de baja, se renombra);
un documento de tránsito emitido y una caravana colocada son hechos que no se reescriben.

### 2. El DT-e liga dos establecimientos por su RENSPA, no toca el ledger

`TransitDocument` registra `dte_number`, `origin`/`destination` (FK a `Establishment`),
fecha, `category`, `head_count` y opcionalmente el `lot` que viajó. No postea asiento:
un tránsito es un hecho documental sanitario, no un cargo. El cobro sigue siendo
exclusivamente del ledger vía `feed` (adr-25).

*Por qué:* un solo camino de cobro. El DT-e es trazabilidad, no economía; ligarlo al
ledger confundiría dos preguntas distintas.

### 3. El DT-e valida en el servicio, no en la vista

`register_transit` rechaza en el **servicio** un `Establishment` inactivo en origen o
destino, un `head_count` no positivo, un origen igual al destino y un `dte_number`
duplicado. La carga tardía con fecha retroactiva se acepta (misma norma de campo que
adr-28).

*Por qué:* las reglas de negocio viven en el servicio, único punto de escritura, para
que vista, admin y comando compartan la misma validación.

### 4. La caravana identifica un animal individual y es única

`Caravana` liga un `official_number` único a un `Animal` con su `assigned_date`. Se
registra al colocarla sobre un animal activo; un animal muerto/vendido/egresado no se
caravanea. La unicidad de `official_number` es a nivel base de datos.

*Por qué:* la caravana oficial es identidad individual permanente; duplicarla rompería
la trazabilidad que existe para garantizar. Un re-caravaneo físico (pérdida de tag) es
una adición futura explícita, no parte de esta fase.

### 5. La cobertura de caravana es una métrica derivada, honesta con el hueco

`apps.metrics` gana `caravana_coverage`: sobre la hacienda **activa** de un cliente,
cuántas cabezas tienen caravana oficial y cuántas no. Sin animales activos la cobertura
es `null` con su motivo, nunca un cero de relleno (adr-29 regla 2).

*Por qué:* "0% de cobertura" y "no hay hacienda que caravanear" son situaciones
opuestas; un cero las confunde, el hueco explícito las distingue.

## Consecuencias

- El backend entra solo por [[API]] (adr-03) y nace por el flujo [[TDD]] (adr-07).
- No se agregan variables de entorno: la app es datos internos, sin integración con el
  sistema de SENASA en esta fase — la emisión/consulta real del DT-e ante SENASA es una
  adición futura explícita, no parte de este cut.
- `livestock` no se refactoriza: la `Caravana` referencia al `Animal` existente, no
  agrega un campo a `Animal` (la extracción mira hacia adelante, adr-32 regla 2).
- Cualquier cambio a las reglas 1–5 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
