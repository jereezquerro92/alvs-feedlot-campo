---
title: adr-33-feedyard-operating-loop
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, feedyard, pens, rations, bunk, phase-7]
---

# ADR-33 — El loop operativo del corral (`feedyard`)

**Contexto:** extiende [[adr-49-domain-layer-and-growth-by-addition]] ("crece por adición") y
[[adr-25-account-ledger]] (el cobro es del ledger, y de nadie más). Nace de evaluar
software de feedlot de la competencia (Cattler): el loop diario dieta → orden de
carga → alimentar → leer comedero → ajustar es el corazón de un feedlot y hoy nos
falta. Reglas solamente; las entidades viven en [[FEEDLOT-DATA-MODEL]].

## Contexto

Hasta la Fase 6 el sistema sabía *qué* comió un animal o lote (`FeedingEvent`) y
*cuánto* costó, pero no conocía el **corral** físico, la **receta** de la dieta, ni
el ciclo de planificación y control que un feedlot corre todos los días. Sin corral
no hay cierre por corral; sin receta no hay materia seca; sin lectura de comedero no
hay ajuste de ración. Se agrega una app `feedyard` que aporta esa capa **operativa y
de monitoreo**, sin tocar cómo se cobra.

## Decisiones

### 1. `feedyard` es planificación y monitoreo; NO cobra

Ningún modelo de `feedyard` postea un asiento. El cobro de alimento sigue siendo
exclusivamente de `feed` vía `register_feeding` (adr-25 regla 4). `feedyard` planea
(`LoadingOrder`), describe (`Ration`) y mide (`BunkScore`); el cargo lo hace `feed`
cuando la ración se ejecuta.

*Por qué:* un solo camino de cobro. Dos apps que puedan debitar la misma cuenta por
el mismo alimento reabren la puerta al doble cargo que la doctrina cerró (un hecho se
afirma una vez, adr-49 regla 5).

### 2. La orden de carga es el PLAN; el `FeedingEvent` es lo EJECUTADO

`LoadingOrder` registra lo que el mixer **debía** llevar a un corral para una ración
(kg como-servido planificados). `FeedingEvent` (extendido con un `pen` opcional)
sigue siendo lo que **realmente** se sirvió, con peso y precio reales, y es lo único
que cobra. No son el mismo hecho duplicado: son plan y ejecución, y su diferencia es
justamente el dato de gestión (¿se cargó de más o de menos que lo planeado?).

*Por qué:* Cattler y cualquier feedlot serio distinguen la orden de carga de la
pesada real del mixer. Fusionarlas pierde el desvío plan-vs-real, que es la métrica
que dice si el comedero se está leyendo bien.

### 3. El `pen` en `FeedingEvent` es aditivo y opcional

Se agrega una FK nullable `pen` a `feed.FeedingEvent`. Los feedings existentes y los
por-animal/lote sin corral siguen siendo válidos; nada se vuelve obligatorio.

*Por qué:* no se reescribe el dominio estable (mismo criterio que adr-32 regla 2). El
corral es información que enriquece el feeding, no una condición nueva para poder
alimentar.

### 4. La ración es una receta, no un ítem costeado

`Ration` + `RationLine` describen la **composición** (qué `FeedType`, en qué
`proportion`, con qué `dry_matter_pct`). La ración no tiene precio propio: el costo
aparece recién cuando se sirve, con el `unit_price` histórico del `FeedingEvent`
(adr-25 regla 3). La materia seca vive en la receta porque el consumo técnico se mide
en materia seca, no en tal-cual.

*Por qué:* separar la fórmula (estable, editable) del precio (histórico, por evento)
evita que editar una receta reescriba el pasado. El `FeedType` es un insumo; la
`Ration` es cómo se combinan — son cosas distintas y no se colapsan.

### 5. Los catálogos se editan; los eventos son inmutables

`Pen`, `Ration` y `RationLine` son datos maestros: CRUD completo. `LoadingOrder` y
`BunkScore` son hechos fechados: list/retrieve/create, sin update ni destroy
(adr-49 regla 3). Una corrección de un evento es otro evento.

*Por qué:* misma postura event-sourced del resto del sistema. Un corral se corrige
(se desactiva, se renombra); una lectura de comedero de ayer no se reescribe.

### 6. Un corral inactivo y una ración inactiva rechazan eventos nuevos

`register_loading_order` y `register_bunk_score` rechazan en el **servicio** (no en la
vista) un `Pen` con `status=inactive`; una `LoadingOrder` rechaza una `Ration`
inactiva. La carga tardía con fecha retroactiva se acepta mientras el corral siga
activo (mismo criterio que adr-28 para animales).

### 7. El cierre por corral, en esta fase, es del lado costo

`apps.metrics` gana un resumen por corral: kilos servidos y costo de alimento por
corral en el período, leídos de `FeedingEvent.pen`. El cierre por **ganancia**
(kg producidos y conversión por corral) necesita placement animal/lote → corral con
movimientos, y se difiere explícitamente a la Fase 7b junto con el mapa de corrales.

*Por qué:* un cierre por ganancia sin saber qué animales estuvieron en el corral y
cuánto pesaron sería un número inventado — exactamente lo que adr-29 prohíbe. Se
entrega lo que se puede afirmar con honestidad (el costo) y se difiere lo que no.

## Consecuencias

- El backend entra sólo por [[API]] (adr-03) y nace por el flujo [[TDD]] (adr-07);
  este ADR no exceptúa ese camino (adr-49 regla 6).
- `feedyard` no gana migraciones que toquen `ledger`; la única migración fuera de la
  app nueva es la FK aditiva `pen` en `feed`.
- La escala 0–4 de `BunkScore` es el estándar de lectura de comedero; su
  interpretación (subir/bajar/mantener ración) es lógica de la Fase 7b/frontend, no
  se hardcodea como cobro ni como acción automática acá.
- Cualquier cambio a las reglas 1–5 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
