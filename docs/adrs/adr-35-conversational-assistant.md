---
title: adr-35-conversational-assistant
type: adr
status: active
created: 2026-07-25
tags: [adr, feedlot, assistant, generative, chatbot, phase-8]
---

# ADR-35 — El asistente conversacional es el tier generador, acotado

**Estado:** activo (Fase 8)
**Contexto:** activa la costura del tier generador que [[adr-15-chatbot-two-tier]]
regla 9 dejó abierta; reusa el precedente generativo acotado de
[[adr-27-advisors-generative]] y el patrón de inferencia de [[adr-31-advisors-implementation]].

## Contexto

El router (Fase router) es el tier que **elige**: enum cerrado, cero generación,
con derechos de actuador. Los asesores (Fase 5) son generación de **informes**
de un tiro por rol. Falta la superficie que todo competidor tiene: **preguntarle
a los datos del cliente en lenguaje natural** y recibir una respuesta fundada —
multi-turno, no un informe cerrado. Esa es la app `assistant`.

`assistant` es el tier que **genera** de [[adr-15-chatbot-two-tier]]: produce
texto libre y es **read-only para siempre**. No es una relajación del router; es
la otra mitad, permanentemente disjunta (adr-15 regla 1).

## Decisiones

### 1. El asistente genera texto y JAMÁS actúa

`assistant` produce prosa analítica sobre los datos de un cliente y nunca ejecuta
una acción, nunca postea un asiento, nunca cambia estado de dominio. Es el tier
generador de adr-15 regla 1: read-only, para siempre. Si algún día quiere disparar
una acción, **re-entra por el router** con su menú cerrado (adr-15 regla 4) — un
camino que esta fase no construye y deja explícitamente fuera de alcance.

*Por qué:* la frontera entre elegir y generar es un invariante permanente de
adr-15, no un arreglo transitorio. Un tier que genere prosa y además accione
reabre exactamente el canal que ese ADR existe para cerrar.

### 2. El scope por cliente es una barrera dura, calcada de los asesores

Cada turno del asistente razona **solo** sobre un `input_snapshot` que arma el
backend para UN cliente (adr-27 regla 2). El asistente no consulta la base, no lee
otro cliente, no ejecuta nada. El snapshot se construye en el servicio con el
`client` de la conversación; no se recibe armado desde afuera (adr-31 regla 2).

### 3. Una sola definición de cada métrica

El snapshot se arma con `apps.advisors.snapshot.build_snapshot`, que lee
`apps.metrics` (Fase 3). El asistente, el asesor y el gráfico que ve el cliente
leen los mismos números — no pueden contradecirse porque son la misma fuente
(adr-31 regla 3). Si la conversión sale "no calculable" en el dashboard, sale
igual para el asistente.

### 4. Cada turno del asistente es un registro auditable

Una `Conversation` es un hilo por cliente; cada `Message` de rol `assistant`
persiste su `input_snapshot`, `model_id`, `tokens` y `latency_ms`. Leer un mensaje
**no** vuelve a inferir (adr-27 regla 3). Se puede ver exactamente qué datos vio el
modelo en cada respuesta.

### 5. Cliente de inferencia calcado del router y de los asesores

`AssistantBedrockClient` (real, `converse`, temperatura 0.3 — genera prosa) y
`MockAssistantClient` (determinista, sin red) con `get_assistant_client` como único
punto de selección, gateado por DEBUG igual que router (adr-15) y asesores
(adr-31 regla 4). Un proceso no-DEBUG solo puede construir el cliente real; ningún
setting fuerza el mock a un deploy. Los tests corren contra el mock.

### 6. Catálogo editable, eventos inmutables

Una `Conversation` se crea y se lista; los `Message` se crean y se leen —
list/retrieve/create, sin update ni destroy (adr-24 regla 3). Un turno es un hecho
fechado: una corrección es otro turno, no editar el pasado.

## Consecuencias

- El backend entra solo por [[API]] (adr-03) y nace por el flujo [[TDD]] (adr-07).
- La inferencia sigue las reglas en vigor: async ([[adr-16-async-mandatory]] regla 4,
  `sync_to_async` sobre `boto3`, nunca `aiobotocore`), sobre Bedrock, gateada por
  DEBUG. `ASSISTANT_BEDROCK_MODEL_ID` entra en [[VARIABLES]] antes de leerse
  ([[adr-03-api-and-backend]] regla 7); reusa `BEDROCK_REGION`.
- Esto es una capa de capacidad, no un cambio de doctrina (precedente adr-13/adr-27):
  Cognito sigue siendo el único autenticador ([[adr-10-auth]]); [[CACHE]] no gana un
  servidor de caché ([[adr-06-cache]]); el router sigue siendo el único con derechos
  de actuador.
- Cualquier cambio a las reglas 1–5 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
