---
title: ADR-45 — El portal del dueño de lote alcanza el asesor conversacional, acotado a su cliente
type: adr
status: active
created: 2026-07-28
tags: [adr, rbac, assistant, tenant-isolation, lot-owners, feedlot, phase-module-first-redesign]
---

# ADR-45 — El portal del dueño de lote alcanza el asesor conversacional, acotado a su cliente

**Contexto:** amplía [[adr-44-field-operational-roles]] decisión 3 (qué rutas alcanza
una sesión `lot_owners`) por el camino que esa misma decisión exige — un ADR nuevo,
nunca una excepción local ([[adr-20-authorization-lobby]] regla 2, precedente de las
excepciones acotadas de [[adr-13-m365-graph]] regla 3). Reusa la barrera per-cliente
read-only de [[adr-27-advisors-generative]] regla 2 y la disjunción permanente
generar/elegir de [[adr-15-chatbot-two-tier]] regla 1. Reglas solamente; el mecanismo
vive en [[AUTH]], la matriz en `apps/users/roles.py` y el contrato de rutas en [[API]].

## Contexto

[[adr-44-field-operational-roles]] decisión 3 confinó al `lot_owners` (portal de
cliente, read-only) a **exactamente dos** superficies keyed por cliente: las métricas
(`/api/metrics/{client_id}/…`) y la cuenta (`/api/clients/{id}/account|ledger|outstanding`),
ambas gateadas por `ClientScopedReadPermission`. El rediseño module-first agrega el
**asesor conversacional** (`assistant`, [[adr-35-conversational-assistant]]) como un
módulo del portal: el dueño de lote pregunta en lenguaje natural sobre **su propia**
hacienda y su saldo, y recibe una respuesta fundada.

Esa lectura es exactamente la que el `lot_owners` ya tiene autorizada sobre sus
métricas — el asesor no ve ni un dato más que los que ya arma el snapshot per-cliente
([[adr-27-advisors-generative]] regla 2). Pero es una **tercera** ruta alcanzable, y
[[adr-44-field-operational-roles]] fijó su lista con la palabra "exactamente" y mandó
que ampliarla exige un ADR (decisión 3 y consecuencia final, reglas 1–7 semánticas).
Este ADR es ese vehículo. No toca el cuerpo de adr-44; lo amplía por adición.

## Decisiones

### 1. El asesor es una tercera superficie alcanzable por `lot_owners`, acotada a su cliente

Una sesión `lot_owners` alcanza `GET/POST /api/conversations/…`
([[adr-35-conversational-assistant]], [[API]]) **únicamente** sobre el cliente ligado a
su `AccessRequest` ([[adr-44-field-operational-roles]] decisión 4). La lista de rutas
per-cliente que la decisión 3 de adr-44 declaró "exactamente" pasa a ser **tres**:
métricas, cuenta y **asesor**. Ninguna otra ruta se abre; esta ampliación es aditiva y
enumerada, no un ensanche general del portal.

*Por qué:* preguntarle al asesor por la propia hacienda es la misma lectura que el
portal ya autoriza sobre las métricas, servida en forma conversacional. Negarla sería
arbitrario; abrirla sin enumerarla reabriría la puerta a un portal de alcance difuso
que adr-44 decisión 3 cerró a propósito.

### 2. La confinación es idéntica a la del portal y falla cerrada

`AssistantAccess` aplica la misma barrera per-cliente que `ClientScopedReadPermission`,
por las tres vías keyed en el cliente ligado ([[adr-44-field-operational-roles]]
decisión 4): en list/create el `client` pedido (query param o body) debe igualar al
ligado; `has_object_permission` re-verifica el cliente de la conversación en una ruta de
detalle; y el queryset del viewset filtra las listas al cliente ligado. Una sesión
`lot_owners` sin cliente ligado no alcanza **nada** — 403, nunca "todos los clientes".

*Por qué:* una frontera entre inquilinos se define una vez y se enforcea igual en cada
puerta. Reusar el mecanismo exacto del portal (no uno paralelo) evita que las dos
superficies se desincronicen y deja una sola definición de "mi cliente".

### 3. El asesor sigue read-only sobre el dominio; preguntar no es actuar

El asesor genera prosa analítica y **jamás** ejecuta una acción, postea un asiento ni
cambia estado de dominio ([[adr-35-conversational-assistant]] decisión 1,
[[adr-15-chatbot-two-tier]] regla 1). Que un `lot_owners` pueda **escribir** un turno
(`POST`) no viola su naturaleza read-only del portal: el POST crea un mensaje sobre su
propia conversación y dispara una lectura generativa sobre su propio snapshot — no muta
ni un registro de dominio del cliente. La disjunción permanente elegir/generar de adr-15
queda intacta: el asesor no es el router y no gana derechos de actuador.

*Por qué:* la regla read-only de adr-44 protege los **datos de dominio** del inquilino,
no prohíbe registrar la pregunta del propio inquilino. El turno es un registro auditable
([[adr-35-conversational-assistant]] decisión 4), no una escritura de dominio.

### 4. Autorización en Django, por Group, per-request

Quién alcanza el asesor se decide leyendo Django Groups en el backend, por request, sin
caché en el camino ([[adr-10-auth]] regla 2, [[adr-20-authorization-lobby]] regla 4). El
frontend gatea la navegación al módulo por comodidad de UX; la barrera es el backend. El
vínculo usuario→cliente lo pone un admin en `/admin/`, nunca es autoservicio
([[adr-44-field-operational-roles]] decisión 4).

*Por qué:* misma doctrina que todo el RBAC del sistema. El portal es una frontera de
seguridad y vive donde vive la autoridad, en Django.

## Consecuencias

- El backend entra solo por [[API]] ([[adr-03-api-and-backend]]): las filas de
  `/api/conversations/…` nombran `AssistantAccess` y su celda de auth documenta la
  confinación `lot_owners`. La clase vive en `apps/users/roles.py`, hogar único de la
  matriz ([[adr-44-field-operational-roles]] decisión 1).
- No hay modelo, migración ni variable de entorno nuevos: esto es una regla de
  autorización sobre rutas ya declaradas ([[adr-35-conversational-assistant]]).
- Las superficies staff-only no cambian: el roster de clientes
  (`ClientDirectoryAccess`) y los informes generativos del asesor de un tiro
  (`AdvisorAccess`) siguen cerrados a `lot_owners` — este ADR abre el asesor
  conversacional per-cliente y nada más.
- Cognito sigue autenticando solamente y el RBAC sigue siendo exclusivamente Django
  Groups ([[adr-10-auth]] reglas 1–2, intactas); el cuerpo de
  [[adr-44-field-operational-roles]] no se edita.
- Cualquier cambio a las reglas 1–4 es semántico y DEBE superseder este ADR
  ([[adr-00-adr-doctrine]] regla 4).
