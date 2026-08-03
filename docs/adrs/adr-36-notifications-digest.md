---
title: adr-36-notifications-digest
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, notifications, digest, whatsapp, phase-9]
---

# ADR-36 — Notificaciones: el digest y el canal de envío

**Contexto:** reusa las métricas de [[adr-29-metrics-derivation]] (una sola
definición de cada número) y el patrón de cliente mock/real gateado por DEBUG de
[[adr-31-advisors-implementation]] y [[adr-35-conversational-assistant]].

## Contexto

Todo competidor empuja resúmenes al cliente sin que el cliente entre a mirar:
un digest semanal por WhatsApp con las cabezas, el saldo y la conversión. Falta la
capa que **arma un resumen y lo manda por un canal**. Esa es la app `notifications`.

## Decisiones

### 1. El digest se arma desde las métricas, no se recalcula

`build_weekly_digest` lee `apps.metrics.services.summary` para UN cliente y lo
renderiza a texto. No define ninguna métrica nueva: el número que ve el cliente en
el digest es el mismo del dashboard y del asesor (adr-29 regla 1, adr-31 regla 3).

*Por qué:* tres consumidores con tres definiciones de "conversión" es exactamente
lo que la doctrina de métricas existe para evitar.

### 2. El envío es una abstracción con mock y real, gateada por DEBUG

`get_sender(channel)` es el único punto de selección: en DEBUG devuelve
`MockSender` (sin red, registra lo enviado); fuera de DEBUG devuelve el sender real
del canal (`WhatsAppSender`). Ningún setting fuerza el mock a un deploy — mismo gate
que los clientes de inferencia (adr-31 regla 4, adr-35 decisión 5). Los tests corren
contra el mock.

*Por qué:* el envío externo depende de credenciales vivas que no existen en test ni
en dev; el mock deja la lógica testeable y el real queda enchufable sin tocar el
flujo.

### 3. Una notificación es un registro inmutable con su estado

`Notification` guarda `client`, `channel`, `to_address`, `subject`, `body`, y un
`status` ∈ {`pending`, `sent`, `failed`} con su `error` y `sent_at`. Se crea y se
lee — list/retrieve/create, sin update ni destroy (adr-24 regla 3). Un reintento es
una notificación nueva, no editar la anterior.

*Por qué:* el registro de qué se mandó, a quién y con qué resultado tiene que ser
auditable; sobrescribir el estado perdería el historial de intentos.

### 4. Notificar no toca el ledger ni actúa sobre el dominio

`notifications` es read-only sobre los datos del cliente: lee métricas, arma texto,
manda. No postea asiento, no cambia estado de dominio. Es una capa de salida, no un
actuador (misma postura que `feedyard`/adr-33 respecto del cobro).

*Por qué:* mandar un resumen es informar, no operar. Un solo camino de cobro sigue
siendo el ledger vía `feed` (adr-25).

## Consecuencias

- El backend entra solo por [[API]] (adr-03) y nace por el flujo [[TDD]] (adr-07).
- `WHATSAPP_TOKEN` y `WHATSAPP_PHONE_NUMBER_ID` entran en [[VARIABLES]] antes de
  leerse ([[adr-03-api-and-backend]] regla 7); sólo los lee `WhatsAppSender`, nunca
  el mock. No son secretos en git — viven en `.env` local o Secrets Manager.
- El comando `send_weekly_digests` arma y manda por cliente; una falla de envío de un
  cliente no frena a los demás (misma disciplina de aislamiento que `ingest_prices`).
- Cualquier cambio a las reglas 1–4 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
