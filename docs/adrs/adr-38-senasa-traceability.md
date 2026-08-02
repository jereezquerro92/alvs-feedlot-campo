---
title: adr-38-senasa-traceability
type: adr
category: backend
use_case: cargar un establecimiento o su RENSPA, registrar un DT-e, caravanear un animal, leer cobertura de caravana
created: 2026-07-25
modified: 2026-08-02
tags: [adr, feedlot, traceability, senasa, renspa, dte, caravana, phase-11]
---

# ADR-38 — Trazabilidad SENASA: RENSPA, DT-e y caravana

## CONTEXT

> El movimiento de hacienda se documenta ante SENASA: cada establecimiento tiene su RENSPA, cada traslado su DT-e y cada animal su caravana. La app `traceability` registra esos tres hechos sin tocar `livestock` ni el ledger.

## ASSERTIONS

1. `Establishment` —un establecimiento con su `renspa`— es catálogo editable con CRUD completo. `TransitDocument` y `Caravana` son hechos fechados: `list`/`retrieve`/`create`, sin `update` ni `destroy` ([[adr-24-feedlot-domain]] regla 3); una corrección o una re-identificación es un registro nuevo.
2. `TransitDocument` registra `dte_number`, origen y destino como FK a `Establishment`, fecha, `category`, `head_count` y opcionalmente el `lot` que viajó. No postea asiento: un tránsito es un hecho documental sanitario, no un cargo.
3. `register_transit` rechaza en el servicio —no en la vista— un establecimiento inactivo en origen o destino, un `head_count` no positivo, un origen igual al destino y un `dte_number` duplicado. La carga tardía con fecha retroactiva se acepta.
4. `Caravana` liga un `official_number` único —unicidad a nivel base de datos— a un `Animal`, con su `assigned_date`. Se registra sobre un animal activo; muerto, vendido o egresado no se caravanea.
5. `apps.metrics` deriva `caravana_coverage`: sobre la hacienda activa de un cliente, cuántas cabezas tienen caravana y cuántas no. Sin animales activos devuelve `null` con su motivo, nunca un cero ([[adr-29-metrics-derivation]] regla 2).
6. `livestock` no se refactoriza: la `Caravana` referencia al `Animal` existente y no le agrega un campo ([[adr-32-multi-rubro-assets]] regla 2). La app no agrega variables de entorno: no hay integración con el sistema de SENASA en este cut.

## FORBIDDEN

- **NEVER** duplicar un `official_number` (regla 4). La caravana es identidad individual permanente, y duplicarla rompe la trazabilidad que existe para garantizar.
- **NEVER** postear un asiento por un tránsito (regla 2). El DT-e es trazabilidad, no economía; ligarlo al ledger confunde dos preguntas distintas.
- **NEVER** editar un DT-e emitido o una caravana colocada (regla 1). Son hechos; la corrección es otro registro.
- **NEVER** validar el tránsito en la vista (regla 3). La regla vive en el servicio, que comparten vista, admin y comando.
- **NEVER** informar 0% de cobertura cuando no hay hacienda activa (regla 5). Son situaciones opuestas y el cero las confunde.

## REJECTED

- **Un campo `caravana` en `Animal`** — la identificación oficial como columna del animal. Rechazado por la regla 6: la extracción mira hacia adelante y `livestock` no se toca; el registro fechado además conserva cuándo se colocó.
- **Integrar la emisión o consulta del DT-e ante SENASA** — hablar con el sistema real. Fuera de alcance explícito de este cut, que registra el documento; la integración entra como adición futura con su propio cambio.
- **El re-caravaneo por pérdida de tag** — un flujo para reemplazar una caravana. No modelado en esta fase; entra explícitamente cuando el caso aparezca, no como efecto lateral de la unicidad.

## RELATED

### related adrs

- [[docs/adrs/adr-24-feedlot-domain]] — regla 3, catálogo editable y evento inmutable
- [[docs/adrs/adr-33-feedyard-operating-loop]] — regla 5, el mismo precedente catálogo/evento
- [[docs/adrs/adr-32-multi-rubro-assets]] — regla 2, la extracción hacia adelante
- [[docs/adrs/adr-29-metrics-derivation]] — regla 2, el hueco honesto de la cobertura

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `Establishment`, `TransitDocument`, `Caravana`
- [[docs/GLOSSARY-feedlot-additions]] — RENSPA, DT-e, caravana
- [[docs/API]] — las rutas de trazabilidad
