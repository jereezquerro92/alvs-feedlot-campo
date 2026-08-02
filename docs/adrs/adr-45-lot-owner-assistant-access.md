---
title: adr-45-lot-owner-assistant-access
type: adr
category: backend
use_case: abrir el asesor conversacional al portal del cliente, gatear /api/conversations/, verificar la confinación por cliente de una sesión lot_owners
created: 2026-07-28
modified: 2026-08-02
tags: [adr, rbac, assistant, tenant-isolation, lot-owners, feedlot]
---

# ADR-45 — El portal del dueño de lote alcanza el asesor conversacional, acotado a su cliente

## CONTEXT

> El dueño de lote pregunta en lenguaje natural por su propia hacienda y su saldo. Es la misma lectura que el portal ya autoriza sobre sus métricas, servida en forma conversacional, y por eso se enumera como tercera superficie en vez de ensanchar el portal.

## ASSERTIONS

1. Una sesión `lot_owners` alcanza `GET`/`POST` de `/api/conversations/…` ([[adr-35-conversational-assistant]]) únicamente sobre el cliente ligado a su `AccessRequest`. La lista que [[adr-44-field-operational-roles]] regla 4 enumera pasa a ser tres: métricas, cuenta y asesor. Ninguna otra ruta se abre.
2. `AssistantAccess` aplica la misma barrera per-cliente que `ClientScopedReadPermission`, por las tres vías: en list y create el `client` pedido debe igualar al ligado; `has_object_permission` re-verifica el cliente de la conversación en una ruta de detalle; y el queryset filtra las listas al cliente ligado. Sin cliente ligado, 403 — nunca "todos los clientes".
3. El asesor sigue read-only sobre el dominio: genera prosa y no ejecuta acciones, no postea asientos ni cambia estado ([[adr-35-conversational-assistant]] regla 1). Que un `lot_owners` cree un turno no viola su naturaleza read-only: el `POST` registra su propia pregunta sobre su propia conversación y dispara una lectura generativa sobre su propio snapshot.
4. Quién alcanza el asesor se decide leyendo Django Groups en el backend, por request y sin caché en el camino ([[adr-10-auth]] regla 2, [[adr-20-authorization-lobby]] regla 4). El frontend gatea la navegación por comodidad; la barrera es el backend. El vínculo usuario→cliente lo pone un admin, nunca es autoservicio.
5. Las superficies staff-only no cambian: el roster de clientes y los informes generativos de un tiro siguen cerrados a `lot_owners`. No hay modelo, migración ni variable nueva: esto es una regla de autorización sobre rutas ya declaradas, y la clase vive en `apps/users/roles.py` ([[adr-44-field-operational-roles]] regla 2).

## FORBIDDEN

- **NEVER** ampliar el portal sin enumerar la ruta en un ADR (regla 1). Un portal de alcance difuso es exactamente lo que [[adr-44-field-operational-roles]] regla 4 cerró con la palabra "exactamente".
- **NEVER** implementar una barrera per-cliente paralela a la del portal (regla 2). Dos mecanismos se desincronizan y dejan dos definiciones de "mi cliente".
- **NEVER** dejar pasar a una sesión sin cliente ligado (regla 2). Falla cerrado, siempre.
- **NEVER** darle al asesor un derecho de actuador para servir al portal (regla 3). La disjunción entre elegir y generar es permanente.
- **NEVER** confiar en el gateo del frontend (regla 4). Es UX; la frontera entre inquilinos vive en Django.

## REJECTED

- **Abrir el asesor a `lot_owners` sin ADR** — tratarlo como una lectura ya autorizada y agregar la ruta. Rechazado: [[adr-44-field-operational-roles]] regla 4 exige el vehículo, y sin él la lista enumerada deja de ser enumerada.
- **Negarle el asesor al portal** — dejarlo staff-only por ser generativo. Rechazado por arbitrario: no ve un dato más que los que el snapshot per-cliente ya arma para las métricas que el portal lee.
- **Una `ClientScopedAssistantPermission` propia, escrita aparte** — una clase gemela con su propia lógica. Perdió contra la regla 2: reusar el mecanismo exacto del portal es lo que impide que las dos superficies se separen.

## RELATED

### related adrs

- [[docs/adrs/adr-44-field-operational-roles]] — reglas 2 y 4, la matriz y la lista de rutas que esto amplía
- [[docs/adrs/adr-35-conversational-assistant]] — el asesor conversacional y su naturaleza read-only
- [[docs/adrs/adr-27-advisors-generative]] — regla 2, la barrera per-cliente que se reusa
- [[docs/adrs/adr-15-chatbot-two-tier]] — regla 1, la disjunción permanente entre elegir y generar
- [[docs/adrs/adr-20-authorization-lobby]] — regla 4, la decisión por request sin caché

### related files

- [[docs/API]] — las filas de `/api/conversations/…` y su celda de auth
- [[docs/AUTH]] — el mecanismo de sesión y grupos
