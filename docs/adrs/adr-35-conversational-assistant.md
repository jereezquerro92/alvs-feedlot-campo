---
title: adr-35-conversational-assistant
type: adr
category: backend
use_case: preguntar en lenguaje natural sobre un cliente, agregar un turno o una conversación, tocar el snapshot o el cliente de inferencia del asistente
created: 2026-07-25
modified: 2026-08-02
tags: [adr, feedlot, assistant, generative, chatbot, phase-8]
---

# ADR-35 — El asistente conversacional es el tier generador, acotado

## CONTEXT

> Preguntarle a los datos de un cliente en lenguaje natural, multi-turno, y recibir una respuesta fundada. `assistant` es el tier que genera de [[adr-15-chatbot-two-tier]]: prosa libre, read-only para siempre, permanentemente disjunto del router que elige.

## ASSERTIONS

1. El asistente produce prosa analítica sobre los datos de un cliente y nunca ejecuta una acción, postea un asiento ni cambia estado de dominio. Es el tier generador de [[adr-15-chatbot-two-tier]] regla 1: read-only, para siempre. Disparar una acción sería re-entrar por el router con su menú cerrado (regla 4 de ese ADR), un camino que esta fase deja fuera de alcance.
2. Cada turno razona sólo sobre un `input_snapshot` que el backend arma para un cliente ([[adr-27-advisors-generative]] regla 2). El asistente no consulta la base, no lee otro cliente y no ejecuta nada; el snapshot se construye en el servicio con el `client` de la conversación y no se recibe armado desde afuera ([[adr-31-advisors-implementation]] regla 2).
3. El snapshot se arma con `apps.advisors.snapshot.build_snapshot`, que lee `apps.metrics`. El asistente, el asesor y el gráfico que ve el cliente leen los mismos números y no pueden contradecirse. Si la conversión sale "no calculable" en el dashboard, sale igual acá.
4. Una `Conversation` es un hilo por cliente y cada `Message` de rol `assistant` persiste su `input_snapshot`, `model_id`, `tokens` y `latency_ms`. Leer un mensaje no vuelve a inferir: se ve exactamente qué datos vio el modelo en cada respuesta.
5. `AssistantBedrockClient` (real, `converse`, temperatura 0.3) y `MockAssistantClient` (determinista, sin red) se eligen en `get_assistant_client`, único punto de selección, gateado por DEBUG igual que el router y los asesores. Un proceso no-DEBUG sólo puede construir el cliente real; los tests corren contra el mock.
6. Conversaciones y mensajes exponen `list`/`retrieve`/`create`, sin `update` ni `destroy` ([[adr-24-feedlot-domain]] regla 3): un turno es un hecho fechado y una corrección es otro turno.
7. La inferencia sigue las reglas en vigor: async con `sync_to_async` sobre `boto3` ([[adr-16-async-mandatory]] regla 4), sobre Bedrock. `ASSISTANT_BEDROCK_MODEL_ID` entra en [[VARIABLES]] antes de leerse ([[adr-51-api-and-backend]] regla 7) y reusa `BEDROCK_REGION`.
8. Es una capa de capacidad, no un cambio de doctrina: Cognito sigue siendo el único autenticador ([[adr-10-auth]]), [[CACHE]] no gana un servidor ([[adr-06-cache]]) y el router sigue siendo el único con derechos de actuador.

## FORBIDDEN

- **NEVER** darle al asistente un derecho de actuador (regla 1). Un tier que genere prosa y además accione reabre exactamente el canal que [[adr-15-chatbot-two-tier]] existe para cerrar.
- **NEVER** aceptar un snapshot armado desde afuera (regla 2). Es la vía por la que los datos de otro cliente entrarían al turno.
- **NEVER** darle al asistente un camino a la base (regla 2). El snapshot es todo lo que ve, y ahí se verifica la barrera.
- **NEVER** re-inferir al leer un mensaje (regla 4). El registro dejaría de decir qué vio el modelo cuando respondió.
- **NEVER** editar o borrar un turno (regla 6). Una corrección es otro turno.

## REJECTED

- **Un solo tier que elija y genere** — un asistente con acceso al menú de acciones del router. Rechazado de plano: es la fusión que [[adr-15-chatbot-two-tier]] regla 1 declara permanentemente prohibida.
- **Construir en esta fase la re-entrada al router** — el camino por el que el asistente pediría una acción con menú cerrado. Fuera de alcance explícito; queda como costura, no como deuda oculta.
- **Definir métricas propias del asistente** — números calculados para la conversación. Rechazado por la regla 3: el asistente y el dashboard tienen que leer la misma fuente.

## RELATED

### related adrs

- [[docs/adrs/adr-15-chatbot-two-tier]] — la disjunción permanente entre elegir y generar
- [[docs/adrs/adr-27-advisors-generative]] — el precedente generativo acotado y el scope por cliente
- [[docs/adrs/adr-31-advisors-implementation]] — el snapshot y el cliente de inferencia que esto calca
- [[docs/adrs/adr-45-lot-owner-assistant-access]] — quién alcanza estas rutas y con qué recorte
- [[docs/adrs/adr-16-async-mandatory]] — regla 4, cómo se llama a Bedrock

### related files

- [[docs/CHATBOT]] — los dos tiers y la frontera entre ellos
- [[docs/VARIABLES]] — `ASSISTANT_BEDROCK_MODEL_ID` y `BEDROCK_REGION`
- [[docs/API]] — las rutas de conversaciones y mensajes
