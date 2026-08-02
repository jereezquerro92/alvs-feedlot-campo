---
title: adr-28-animal-lifecycle-and-sanitary
type: adr
category: backend
use_case: registrar un pesaje, una muerte o una salida, cargar una aplicación sanitaria, calcular GDP de un lote, tocar la app sanitary
created: 2026-07-21
modified: 2026-08-02
tags: [adr, feedlot, livestock, sanitary, lifecycle, phase-2]
---

# ADR-28 — Ciclo del animal y la app `sanitary`

## CONTEXT

> Qué le pasó al animal después de entrar y comer: cuánto engordó, si murió, cuándo salió y qué sanidad recibió. Los tres eventos de ciclo de vida comparten forma pero no tabla, y la sanidad siempre se cobra.

## ASSERTIONS

1. `Weighing`, `Death` y `Exit` heredan del abstracto `LifecycleEvent`, que aporta el par `animal`/`lot` y su restricción XOR ([[adr-26-livestock-individual-and-lot]] regla 3). Cada uno mantiene su propia tabla.
2. El GDP de un lote se compara por cabeza (`total_weight / head_count`). Si el `head_count` difiere entre los dos pesajes, el período se reporta con `adg = null` y `not_calculable = "head_count_changed"`: el total de un lote se mueve por ingresos, muertes y salidas, no sólo por engorde.
3. Una muerte no genera asiento — el alimento y la sanidad ya consumidos quedan cobrados y una muerte no los revierte. Una salida tampoco los revierte, y en sus tipos `transfer`/`other` no postea nada.
4. La salida-venta (`Exit.kind=sale`) sí liquida, según [[adr-43-sale-settlement]]: hacienda de cliente (`kind=boarding`) paga una comisión de engorde como débito de servicio; hacienda propia (`kind=own`) registra el producido como crédito en la cuenta propia. El `sale_price_per_kg` es el precio que esa liquidación fotografía ([[adr-25-account-ledger]] regla 3).
5. La app del dominio sanitario se llama `sanitary`, porque `apps.health` es el liveness probe del template y el probe es contrato con el orquestador.
6. Toda aplicación sanitaria se cobra: `register_health_event` siempre postea un débito. No existe el equivalente al `origin=client_stock` de la alimentación, porque los productos sanitarios los pone siempre el feedlot.
7. Los eventos de ciclo de vida son inmutables: los viewsets exponen `list`/`retrieve`/`create`, sin `update` ni `destroy`. Un animal muerto o vendido rechaza pesajes y sanidad posteriores; la carga tardía con fecha retroactiva se acepta mientras el target siga activo.

## FORBIDDEN

- **NEVER** calcular el GDP de un lote sobre el peso total (regla 2). El total lo mueve el rodeo entrando y saliendo, así que el número mediría cualquier cosa menos crecimiento.
- **NEVER** rellenar un GDP no calculable con una estimación (regla 2). Un número plausible y falso se grafica igual que uno real ([[adr-29-metrics-derivation]] regla 2).
- **NEVER** revertir cargos por una muerte de forma automática (regla 3). Sería convertir al feedlot en asegurador del cliente, que es una decisión comercial; si se toma, entra como un `adjustment` explícito y auditable.
- **NEVER** renombrar `apps.health` para liberar el nombre (regla 5). El probe es contrato con el orquestador; lo que se renombra es el dominio nuevo.
- **NEVER** exponer `update` o `destroy` sobre un evento de ciclo de vida (regla 7). Una corrección es otro evento.

## REJECTED

- **Una tabla única de eventos polimórficos** — `Weighing`, `Death` y `Exit` en una sola tabla con un campo tipo. Perdió por los campos nulables que obliga en cada fila y el filtro por tipo en cada consulta; el abstracto comparte la restricción sin fusionar los dominios.
- **Un `origin=client_stock` para sanidad** — el equivalente sanitario del alimento que trae el cliente. Rechazado como complejidad especulativa: hoy los productos los pone siempre el feedlot. Reabre el día que un cliente traiga su propia vacuna, agregando el campo entonces.
- **Llevar stock sanitario en esta fase** — existencias además de aplicaciones, replicando `FeedStockMovement`. No se tomó: el volumen es bajo y el problema real de las vacunas es el vencimiento y la cadena de frío, no el saldo. El patrón queda disponible para cuando ese problema se resuelva de verdad; [[adr-40-sanitary-plan-schedule]] agregó el calendario sin tocar esto.
- **La venta como hecho del cliente, sin huella económica** — la política que este ADR sostuvo hasta [[adr-43-sale-settlement]]: `sale_price_per_kg` era informativo y ninguna salida posteaba. Reemplazada por la regla 4 con el consentimiento del dueño; las muertes siguen sin tocar el ledger.

## RELATED

### related adrs

- [[docs/adrs/adr-26-livestock-individual-and-lot]] — regla 3, el XOR que el abstracto aporta
- [[docs/adrs/adr-25-account-ledger]] — qué cobra el ledger y qué no
- [[docs/adrs/adr-43-sale-settlement]] — la liquidación de la regla 4
- [[docs/adrs/adr-29-metrics-derivation]] — el contrato del "no calculable" de la regla 2
- [[docs/adrs/adr-40-sanitary-plan-schedule]] — el plan sanitario sobre estos eventos

### related files

- [[docs/FEEDLOT-DATA-MODEL]] — `LifecycleEvent`, `Weighing`, `Death`, `Exit`, `HealthEvent`
- [[docs/FEEDLOT]] — el ciclo del animal en la operación
- [[docs/API]] — las rutas de ciclo de vida y sanidad
