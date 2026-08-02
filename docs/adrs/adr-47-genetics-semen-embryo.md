---
title: adr-47-genetics-semen-embryo
type: adr
category: backend
use_case: cargar un toro o sus DEP, mover pajuelas o embriones, registrar una colecta, vender semen, leer stock genético
created: 2026-07-28
modified: 2026-08-02
tags: [adr, feedlot, genetics, semen, embryo, inventory, event-sourced]
---

# ADR-47 — Genética: semen, DEP y transferencia embrionaria (`genetics`)

## CONTEXT

> La genética como activo de primera clase: toros propios y externos, pajuelas en el termo, sus DEP, y la transferencia embrionaria. El inventario se lleva por movimientos y el único hecho económico que sale de la app es la venta de semen.

## ASSERTIONS

1. `genetics` separa catálogos editables —`Sire`, `SemenBatch`, `EmbryoBatch`, `BreedingValue`, con CRUD completo— de hechos fechados inmutables —`SemenMovement`, `EmbryoMovement`, `EmbryoFlush` y `SemenSale`, con `list`/`retrieve`/`create` y sin `update` ni `destroy` ([[adr-24-feedlot-domain]] regla 3).
2. El stock de un `SemenBatch` se deriva de sus movimientos y el de un `EmbryoBatch` de los suyos —Σ entradas − Σ salidas—, exactamente como `FeedStockMovement` ([[adr-25-account-ledger]] regla 4) e `InputStockMovement` ([[adr-37-inventory-and-weather]] regla 1). Nunca se guarda un `straws_remaining` editable.
3. Un `Sire` referencia opcionalmente un `Animal` propio (`category=bull`) o representa un toro externo cuyo semen se compra sin poseer el animal. Un `BreedingValue` es un DEP por toro —`trait`, `value`, `accuracy`, `source`, `date`— y es dato de catálogo que se carga, no una métrica derivada de los eventos del sistema: los publica la evaluación genética, no los pesajes propios.
4. `SemenSale` postea un `credit` `concept=sale` a la cuenta propia por el producido, vía `(source_kind="semen_sale", source_id=<SemenSale.id>)` ([[adr-24-feedlot-domain]] regla 4), y descuenta un `SemenMovement` `out` con `reason=sale`. Fotografía `unit_price × straws` del día ([[adr-25-account-ledger]] regla 3), mismo precedente que la venta de hacienda propia ([[adr-43-sale-settlement]] regla 3). El comprador es informativo.
5. `EmbryoFlush` registra la colecta sobre una donante con su toro y su grado, y produce inventario: crea o actualiza un `EmbryoBatch` y postea un `EmbryoMovement` `in`. El transfer a una receptora no vive acá: es un `Service` con `method=embryo_transfer` en `breeding` ([[adr-46-breeding-reproduction]] regla 7) que descuenta el `out`.
6. Ningún movimiento ni colecta postea asiento: producción y consumo propios no son insumos entregados. El `unit_cost` de una compra de pajuelas es informativo y no genera cargo; el único asiento de la app es el crédito de venta.
7. `register_semen_movement` rechaza una partida inactiva y una `quantity` no positiva; `register_semen_sale` rechaza stock insuficiente y un precio no positivo, y arma el crédito y el `out` en una transacción; las funciones de embriones validan igual. Un stock que quede negativo por carga parcial se muestra como inconsistencia, no se bloquea ([[adr-29-metrics-derivation]] regla 5).
8. `apps.metrics` deriva stock de pajuelas por partida y por toro, semen disponible total y uso por toro en el período. Sin movimientos devuelven `null` con su `not_calculable`, nunca un cero de relleno.
9. `method`, `reason`, `trait`, `grade`, `direction` y demás enums son inglés ([[LOCALIZATION]]); las etiquetas en español existen sólo en el render.

## FORBIDDEN

- **NEVER** guardar un contador editable de pajuelas o embriones (regla 2). Pierde la historia de por qué cambió el stock de un termo.
- **NEVER** postear un asiento por un movimiento o una colecta (regla 6). El consumo propio ya está valuado por el stock; el único hecho económico es la venta.
- **NEVER** calcular un DEP desde los pesajes propios (regla 3). Los publica la evaluación genética; derivarlos acá inventaría un número que nadie firma.
- **NEVER** registrar el transfer embrionario en `genetics` (regla 5). Es un hecho reproductivo sobre un animal y pertenece a `breeding`.
- **NEVER** vender más pajuelas de las que hay (regla 7). El crédito y el `out` se arman juntos, en una transacción.

## REJECTED

- **Cobrarle además al cliente comprador de semen** — un débito en su cuenta junto al crédito propio. Fuera de alcance: entra por el mismo seam con su propio cambio, no en este cut.
- **Facturar el semen consumido en una IA propia** — tratar la pajuela como insumo entregado. Rechazado por la regla 6: es costo interno ya valuado; el cargo por inseminación al cliente boarding lo decide `breeding` ([[adr-46-breeding-reproduction]] regla 6).
- **Un campo de genética en `Animal`** — el toro y sus valores colgados del animal. Rechazado por el precedente de [[adr-32-multi-rubro-assets]] regla 2: `Sire.animal` referencia al `Animal` existente sin agregarle nada.

## RELATED

### related adrs

- [[docs/adrs/adr-46-breeding-reproduction]] — el consumidor: el servicio que descuenta semen o embrión
- [[docs/adrs/adr-25-account-ledger]] — reglas 3 y 4, el precio del día y el stock por movimientos
- [[docs/adrs/adr-37-inventory-and-weather]] — regla 1, el patrón de stock generalizado
- [[docs/adrs/adr-43-sale-settlement]] — regla 3, el precedente del crédito `sale` en la cuenta propia
- [[docs/adrs/adr-29-metrics-derivation]] — el hueco honesto y la inconsistencia que se muestra

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `Sire`, `BreedingValue`, `SemenBatch`, `EmbryoBatch` y sus movimientos
- [[docs/GLOSSARY-feedlot-additions]] — los nombres genéticos, antes del primer uso
- [[docs/API]] — las rutas de `genetics`
