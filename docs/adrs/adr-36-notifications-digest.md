---
title: adr-36-notifications-digest
type: adr
category: backend
use_case: armar o cambiar el digest semanal, agregar un canal de envío, mandar una notificación, testear el envío sin credenciales
created: 2026-07-25
modified: 2026-08-02
tags: [adr, feedlot, notifications, digest, whatsapp, phase-9]
---

# ADR-36 — Notificaciones: el digest y el canal de envío

## CONTEXT

> Empujarle al cliente un resumen sin que entre a mirar: cabezas, saldo y conversión, por WhatsApp. `notifications` arma el texto desde las métricas y lo manda; no calcula nada propio y no opera sobre el dominio.

## ASSERTIONS

1. `build_weekly_digest` lee `apps.metrics.services.summary` para un cliente y lo renderiza a texto. No define ninguna métrica nueva: el número del digest es el mismo del dashboard y del asesor ([[adr-29-metrics-derivation]] regla 1).
2. `get_sender(channel)` es el único punto de selección: en DEBUG devuelve `MockSender` —sin red, registra lo enviado— y fuera de DEBUG el sender real del canal. Ningún setting fuerza el mock a un deploy, mismo gate que los clientes de inferencia; los tests corren contra el mock.
3. `Notification` guarda `client`, `channel`, `to_address`, `subject`, `body` y un `status` ∈ {`pending`, `sent`, `failed`} con su `error` y `sent_at`. Se crea y se lee, sin `update` ni `destroy` ([[adr-24-feedlot-domain]] regla 3): un reintento es una notificación nueva.
4. `notifications` es read-only sobre los datos del cliente: lee métricas, arma texto y manda. No postea asiento ni cambia estado de dominio — es una capa de salida, no un actuador.
5. `WHATSAPP_TOKEN` y `WHATSAPP_PHONE_NUMBER_ID` entran en [[VARIABLES]] antes de leerse ([[adr-51-api-and-backend]] regla 7) y sólo los lee el sender real. Viven en `.env` local o en Secrets Manager, nunca en git.
6. El comando `send_weekly_digests` arma y manda por cliente, y una falla de envío de un cliente no frena a los demás — misma disciplina de aislamiento que `ingest_prices` ([[adr-30-market-prices-connectors]] regla 7).

## FORBIDDEN

- **NEVER** recalcular una métrica dentro del digest (regla 1). El cliente leería en el mensaje un número distinto del que ve en pantalla.
- **NEVER** seleccionar el sender fuera de `get_sender` (regla 2). Dos puntos de selección son dos políticas y una se olvida del gate.
- **NEVER** dejar que un setting fuerce el mock fuera de DEBUG (regla 2). Un deploy que "manda" sin mandar parece sano.
- **NEVER** sobrescribir el estado de una notificación (regla 3). Se perdería el historial de intentos, que es justamente lo que hay que auditar.
- **NEVER** postear un asiento desde `notifications` (regla 4). Informar no es operar; el cobro sigue siendo del ledger vía `feed`.

## REJECTED

- **Reintentar editando la notificación fallida** — un contador de intentos sobre la misma fila. Rechazado por la regla 3: el registro de qué se mandó y con qué resultado se pierde en cuanto se reescribe.
- **Un `try/except` global en el comando** — una sola captura para todo el lote. Perdió contra la regla 6: la falla de un cliente frenaría o silenciaría a los demás.

## RELATED

### related adrs

- [[docs/adrs/adr-29-metrics-derivation]] — la única definición de cada número del digest
- [[docs/adrs/adr-31-advisors-implementation]] — regla 4, el gate mock/real por DEBUG
- [[docs/adrs/adr-30-market-prices-connectors]] — regla 7, el aislamiento por ítem del comando
- [[docs/adrs/adr-24-feedlot-domain]] — regla 3, el registro inmutable

### related files

- [[docs/VARIABLES]] — `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`
- [[docs/FEEDLOT-DATA-MODEL]] — `Notification`
- [[docs/API]] — las rutas de notificaciones
