---
title: adr-28-animal-lifecycle-and-sanitary
type: adr
status: active
created: 2026-07-21
tags: [adr, feedlot, livestock, sanitary, lifecycle, phase-2]
---

# ADR-28 — Ciclo del animal y la app `sanitary`

**Estado:** activo (Fase 2)
**Contexto:** extiende [[adr-24-feedlot-domain]], [[adr-25-account-ledger]] y [[adr-26-livestock-individual-and-lot]].

## Contexto

La Fase 1 dejó el animal entrando al sistema y comiendo, pero sin forma de
registrar qué le pasó después: cuánto engordó, si se murió, cuándo salió, ni qué
sanidad recibió. Sin eso no hay trazabilidad ni conversión alimenticia, que es la
métrica que justifica el sistema.

## Decisiones

### 1. Los eventos de ciclo de vida comparten forma, no tabla

`Weighing`, `Death` y `Exit` heredan de un modelo abstracto `LifecycleEvent` que
aporta el par `animal`/`lot` y la restricción XOR de [[adr-26-livestock-individual-and-lot]].
Cada uno mantiene su propia tabla.

*Por qué:* los tres necesitan idénticamente "exactamente un target", y una tabla
única de eventos polimórficos obliga a campos nulables por todos lados y a filtrar
por tipo en cada consulta. El abstracto evita que las tres restricciones se
desincronicen sin fusionar dominios distintos.

### 2. El GDP de lotes se calcula por cabeza, y se declara no calculable cuando cambia el rodeo

Entre dos pesajes de un lote, el peso comparado es `total_weight / head_count`.
Si el `head_count` difiere entre ambos pesajes, el período se reporta con
`adg = null` y `not_calculable = "head_count_changed"`.

*Por qué:* el total de un lote se mueve por ingresos, muertes y salidas, no solo
por engorde. Un GDP calculado sobre el total mide cualquier cosa menos crecimiento.
La alternativa —estimar contra un peso teórico— produce un número plausible y
falso; un hueco explícito es preferible a un dato que nadie puede auditar.

### 3. Las muertes no tocan el ledger; la salida-venta se liquida por [[adr-43-sale-settlement]]

Una **muerte** (`Death`) no genera asiento: el alimento y la sanidad ya consumidos
quedan cobrados y una muerte no los revierte. Una **salida** (`Exit`) tampoco revierte
esos cargos; y en su tipo `transfer`/`other` (retiro sin venta) sigue sin postear nada.
La **salida-venta** (`Exit.kind=sale`) **sí liquida**, según el modelo comercial que fijó
el dueño y que rige [[adr-43-sale-settlement]]: hacienda de cliente (`kind=boarding`)
cobra una comisión de engorde (débito de servicio); hacienda propia (`kind=own`) registra
el producido como crédito en la cuenta propia. El `sale_price_per_kg` de la salida dejó de
ser meramente informativo: es el precio que la liquidación fotografía
([[adr-25-account-ledger]] regla 3).

*Por qué:* el ledger cobra insumos entregados, y por eso una muerte no revierte cargos —
hacerlo convertiría al feedlot en asegurador del cliente, decisión comercial y no técnica;
si algún día se toma, entra como un `adjustment` explícito y auditable, no como efecto
colateral automático. La venta es distinta: el dueño definió que la hotelería cobra por el
engorde y que la hacienda propia produce un ingreso propio, y esa liquidación llega como su
propio ADR ([[adr-25-account-ledger]] regla 6), sin mutar ningún asiento existente.

### 4. La app se llama `sanitary`, no `health`

El template ya usa `apps.health` para el liveness probe (`/api/health/`).

*Por qué:* colisión de nombre. Se renombra el dominio nuevo, no la infraestructura
existente, porque el probe es contrato con el orquestador. La documentación previa
(`02-modelo-de-datos.md`, `07-arquitectura-escalable-y-roadmap.md`) menciona
`health` y queda desactualizada en ese punto.

### 5. Toda aplicación sanitaria se cobra

`register_health_event` siempre postea un débito. No existe el equivalente al
`origin = client_stock` de la alimentación.

*Por qué:* los productos sanitarios los pone siempre el feedlot. Modelar un origen
que nunca se usa es complejidad especulativa. Si mañana un cliente trae su propia
vacuna, se agrega el campo entonces.

### 6. No se lleva stock sanitario en esta fase

Se registran aplicaciones, no existencias. El patrón de `FeedStockMovement` está
disponible para replicar si hace falta.

*Por qué:* el volumen es bajo y el problema real de las vacunas es el vencimiento y
la cadena de frío, no el saldo. Resolver mal el problema fácil ahora complica
resolver bien el difícil después.

## Consecuencias

- Los eventos de ciclo de vida son inmutables: los viewsets exponen list/retrieve/create,
  deliberadamente sin update ni destroy.
- Un animal muerto o vendido rechaza pesajes y sanidad posteriores. La carga tardía
  con fecha retroactiva **sí** se acepta mientras el target siga activo.
- El consumo de un animal muerto queda cobrado. Si el negocio decide lo contrario,
  entra por contra-asiento manual.
