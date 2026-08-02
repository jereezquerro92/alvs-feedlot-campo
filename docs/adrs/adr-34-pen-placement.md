---
title: adr-34-pen-placement
type: adr
category: backend
use_case: mover hacienda de corral, leer ocupación o cabezas por corral, atribuir un animal a un corral en una fecha
created: 2026-07-25
modified: 2026-08-02
tags: [adr, feedlot, feedyard, pens, placement, phase-7b]
---

# ADR-34 — Ubicación de hacienda en corrales (`PenPlacement`)

## CONTEXT

> Dónde está cada animal: el hecho que faltaba para que el corral fuera algo más que un rótulo sobre el feeding. Se registra como movimiento fechado, y la ocupación se deriva de esos movimientos.

## ASSERTIONS

1. `PenPlacement` registra un movimiento fechado de un `Animal` o un `Lot` hacia adentro (`direction=in`) o hacia afuera (`direction=out`) de un `Pen`. La ubicación actual y la ocupación se derivan de esos eventos y nunca se guardan como campo editable en `Pen` ni en `Animal` ([[adr-24-feedlot-domain]] regla 3).
2. Un `PenPlacement` apunta a un `Animal` o a un `Lot`, nunca ambos ni ninguno: `CHECK` con dos FK nulables, idéntico al de los eventos de ciclo de vida ([[adr-26-livestock-individual-and-lot]] regla 3). Para un lote, `head_count` permite mover una parte; el animal individual no se fracciona.
3. `PenPlacement` no postea ningún asiento: mover hacienda de corral es logística interna, no un insumo entregado. El cobro sigue exclusivamente en `feed` ([[adr-25-account-ledger]] regla 4), como todo `feedyard` ([[adr-33-feedyard-operating-loop]] regla 1).
4. `register_placement` rechaza en el servicio —no en la vista— un `Pen` con `status=inactive` y un `Animal` que no esté `active`: muerto, vendido o egresado no se ubica. La carga tardía con fecha retroactiva se acepta mientras el corral siga activo.
5. `apps.metrics` deriva por corral la ocupación actual en cabezas, las cabezas ingresadas y egresadas del período y los kilos alimentados. La conversión por corral la completa [[adr-42-pen-conversion-honest-cut]], que usa estos eventos para atribuir el engorde.
6. `Pen` no tiene FK a cliente: un corral aloja hacienda de varios clientes, y es el placement el que liga cada cabeza a su corral y —vía el animal o el lote— a su dueño.

## FORBIDDEN

- **NEVER** guardar la ubicación como campo mutable en `Animal` o `Pen` (regla 1). Un feedlot mueve hacienda todo el tiempo, y el campo perdería de qué corral vino y cuánto estuvo.
- **NEVER** postear un asiento por un movimiento de corral (regla 3). La ubicación es información de gestión, no un hecho económico.
- **NEVER** ubicar un animal que no está activo (regla 4). Muerto, vendido o egresado no ocupa un corral.
- **NEVER** validar el corral o el animal en la vista (regla 4). La regla vive en el servicio, único punto de escritura.
- **NEVER** ligar un corral a un cliente (regla 6). El corral es del feedlot y aloja hacienda de varios dueños a la vez.

## REJECTED

- **Un campo `Animal.pen` mutable** — la ubicación como estado, más simple de leer. Rechazado por la regla 1: pierde la historia entera, que es justamente lo que hace auditable el cierre por corral.
- **Una tabla polimórfica de "unidad de hacienda"** — un solo target para el placement. Rechazado por el mismo motivo que en [[adr-26-livestock-individual-and-lot]] regla 3: indirección en cada consulta a cambio de nada.
- **La conversión por corral en esta fase** — cerrar ganancia junto con ocupación. Diferida por honestidad de la métrica y resuelta después por [[adr-42-pen-conversion-honest-cut]], que atribuye sólo los tramos limpios.

## RELATED

### related adrs

- [[docs/adrs/adr-33-feedyard-operating-loop]] — la fase que dejó el corral sin hacienda ubicada
- [[docs/adrs/adr-26-livestock-individual-and-lot]] — regla 3, el XOR que este evento reusa
- [[docs/adrs/adr-42-pen-conversion-honest-cut]] — lo que se deriva sobre estos movimientos
- [[docs/adrs/adr-29-metrics-derivation]] — el hueco explícito en vez del número inventado

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `PenPlacement` y `Pen`
- [[docs/API]] — las rutas de placement
