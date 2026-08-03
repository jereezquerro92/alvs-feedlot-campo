---
title: adr-37-inventory-and-weather
type: adr
category: backend
use_case: cargar un insumo que no es alimento, registrar una entrada o salida de stock, anotar lluvia o clima, leer stock actual
created: 2026-07-25
modified: 2026-08-03
tags: [adr, feedlot, inventory, weather, stock, phase-10]
---

# ADR-37 — Inventario general de insumos y registro de clima

## CONTEXT

> Dos hechos que faltaban: cuánto insumo hay —gasoil, postes, alambre, sanitarios de campo— y cuánto llovió. El stock se generaliza del patrón por movimientos del alimento; ninguno de los dos toca el ledger.

## ASSERTIONS

1. `InputStockMovement` registra entradas y salidas fechadas de un `InputType` por `(owner_kind, client)`, y el stock actual se deriva —Σ entradas − Σ salidas— exactamente como `FeedStockMovement` ([[adr-25-account-ledger]] regla 4). Nunca se guarda un campo `stock` editable en `InputType`.
2. `InputType` es catálogo editable con CRUD completo: "cargar insumos" es crear tipos. `InputStockMovement` es un hecho fechado: `list`/`retrieve`/`create`, sin `update` ni `destroy` ([[adr-24-feedlot-domain]] regla 3), y una corrección es otro movimiento.
3. Ningún `InputStockMovement` postea asiento. Un insumo comprado para el feedlot es consumo propio, no un insumo entregado a un cliente ([[adr-32-multi-rubro-assets]] regla 4). El `unit_price` de una entrada es informativo —valúa el stock— y no genera cargo.
4. `register_input_movement` rechaza en el servicio —no en la vista— un `InputType` con `is_active=False` y una `quantity` no positiva. La carga tardía con fecha retroactiva se acepta, y un stock que quede negativo por carga parcial se muestra como inconsistencia en vez de bloquearse ([[adr-29-metrics-derivation]] regla 5).
5. `WeatherLog` registra por fecha y `site` la lluvia (`rainfall_mm`) y, opcionalmente, temperatura mínima y máxima y una nota. Idempotente por `(site, date)`: re-registrar actualiza la fila, no duplica. No postea asiento y no referencia hacienda ni cuenta: es contexto ambiental que las métricas leen.
6. `apps.metrics` gana dos lecturas puras —stock actual por insumo y resumen de lluvia del período— sin definir ningún número nuevo del negocio ([[adr-29-metrics-derivation]] regla 1). `Animal`, `Lot` y `feed` no se refactorizan: la extracción mira hacia adelante ([[adr-32-multi-rubro-assets]] regla 2).

## FORBIDDEN

- **NEVER** guardar un stock editable en `InputType` (regla 1). Un saldo escrito a mano pierde la historia de por qué cambió.
- **NEVER** postear un asiento por un movimiento de insumo (regla 3). Es consumo propio, y el único camino de cobro sigue siendo el ledger vía `feed`.
- **NEVER** bloquear una carga porque el stock quede negativo (regla 4). El operador falsearía la fecha, y ahí el dato se pierde de verdad.
- **NEVER** validar el insumo en la vista (regla 4). La regla vive en el servicio, que comparten vista, admin y comando.
- **NEVER** acoplar `WeatherLog` a hacienda o a una cuenta (regla 5). La lluvia es contexto para decidir, no una transacción.

## REJECTED

- **Copiar `FeedStockMovement` por cada insumo** — un modelo de stock por tipo de cosa. Es la duplicación que dispara la extracción: un solo movimiento genérico cubre todos y deja uno solo que mantener.
- **Migrar el alimento al stock genérico** — unificar `FeedStockMovement` dentro de `inventory`. Rechazado por el mismo criterio de [[adr-32-multi-rubro-assets]] regla 2: reescribir lo que funciona sólo por simetría es riesgo sin retorno.
- **Cobrar el insumo al cliente desde acá** — facturar gasoil o alambre como servicio. Fuera de alcance: si algún día se factura, entra por el par genérico `(source_kind, source_id)` con su propio cambio.

## RELATED

### related adrs

- [[docs/adrs/adr-25-account-ledger]] — regla 4, el patrón de stock por movimientos que esto generaliza
- [[docs/adrs/adr-32-multi-rubro-assets]] — reglas 2 y 4, la extracción hacia adelante y el consumo propio
- [[docs/adrs/adr-29-metrics-derivation]] — reglas 1 y 5, derivar y mostrar la inconsistencia
- [[docs/adrs/adr-47-genetics-semen-embryo]] — el mismo patrón aplicado a pajuelas y embriones

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `InputType`, `InputStockMovement`, `WeatherLog`
- [[docs/API]] — las rutas de inventario y clima
