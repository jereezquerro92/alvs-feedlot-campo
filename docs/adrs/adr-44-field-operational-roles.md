---
title: adr-44-field-operational-roles
type: adr
category: backend
use_case: gatear un endpoint por rol, editar la matriz de permisos, ligar un usuario a su cliente, abrir una ruta al portal del dueño de lote
created: 2026-07-27
modified: 2026-08-02
tags: [adr, rbac, auth, roles, feedlot]
---

# ADR-44 — Los seis roles operativos del campo y el scoping por cliente

## CONTEXT

> Seis funciones reales del campo, cada una con su recorte de lo que ve y lo que carga. Una de ellas —el dueño de lote— es un portal de cliente: ve UN cliente y ninguno más, y ese recorte es una frontera de aislamiento entre inquilinos, decidida y enforceada en el backend.

## ASSERTIONS

1. Los seis roles son grupos Django creados por migración: `field_managers`, `feed_operators`, `lot_owners`, `field_admins`, `feedlot_owners` y `workshop`. `admins` conserva el superset y `ai_operators` sigue siendo sólo del router. La autorización se decide por membresía de Group, leída en Django y nunca en un claim de Cognito ([[adr-10-auth]] regla 2); sus nombres entran en [[GLOSSARY]] antes del primer uso. Toda la matriz rol → área → método vive centralizada en `apps/users/roles.py` (`GroupMatrixPermission`, con `read_groups` y `write_groups` por área funcional): un viewset sólo referencia su clase de área, y ajustar quién puede qué es editar ese único archivo.
2. `GroupMatrixPermission` acepta métodos seguros si el usuario está en `read_groups` y métodos de escritura si está en `write_groups`; `admins` pasa siempre. Un rol puede leer un área sin poder escribirla.
3. `lot_owners` es read-only y su alcance son exactamente las rutas keyed por cliente que enumeran esta regla y [[adr-45-lot-owner-assistant-access]] regla 1: las métricas, la cuenta del cliente y el asesor conversacional. `ClientScopedReadPermission` compara el `client_id` de la ruta contra el cliente ligado a la sesión y rechaza si no coincide. No se les expone ninguna tabla cruda de dominio.
4. El vínculo usuario→cliente es un FK nullable `client` en `AccessRequest`, que setea un admin en `/admin/` ([[adr-20-authorization-lobby]] regla 3), nunca autoservicio. Un `lot_owners` sin cliente ligado no ve ningún cliente —falla cerrado—, jamás todos. El campo no otorga autoridad: la membresía al grupo activa el scoping y `client` sólo dice cuál.
5. `feedlot_owners`, `field_managers` y `admins` leen sin recorte por cliente: son roles internos del feedlot, no inquilinos. El scoping de la regla 3 aplica sólo a `lot_owners`.
6. No existe un endpoint de débito manual: "cargar deudas" se cumple con los eventos que ya postean y con `Payment`, todos escribibles por `field_managers`. Un ajuste manual, si el negocio lo pide, entra por [[API]] con su propio cambio y nunca mutando un asiento ([[adr-25-account-ledger]] regla 1).
7. Todo endpoint declara su clase de permiso en [[API]] antes del código ([[adr-51-api-and-backend]] regla 1): la columna Auth nombra la clase, y por lo tanto los grupos, que protegen la ruta.
8. `/api/me/` expone el cliente ligado para que el frontend recorte la UI. Ese gateo es comodidad; la barrera es el backend.

## FORBIDDEN

- **NEVER** dejar que un `lot_owners` alcance una ruta fuera de la lista enumerada (regla 3). El portal es una frontera entre inquilinos, y ampliarla exige un ADR, nunca una excepción local.
- **NEVER** darle acceso por defecto a un `lot_owners` sin cliente ligado (regla 4). Falla cerrado; lo contrario expone a todos los clientes por un campo vacío.
- **NEVER** dispersar la matriz de permisos por los viewsets (regla 1). Repartida en cincuenta archivos se desincroniza y deja de ser auditable.
- **NEVER** decidir un permiso en el frontend (regla 8). El gateo de navegación es UX; la barrera vive en Django.
- **NEVER** abrir un endpoint de débito manual (regla 6). El ledger es inmutable y la comodidad no justifica abrir una escritura directa al asiento.

## REJECTED

- **Aislar al `lot_owners` por queryset en cada modelo** — filtrar los ~15 modelos por su camino al cliente. Rechazado por superficie: un solo error en un camino filtra datos de otro inquilino. Confinar el portal a las rutas ya keyed por `client_id` reduce todo a una comparación testeable.
- **Que el usuario elija su cliente** — el vínculo declarado por quien pide acceso. Rechazado por la regla 4: es la misma puerta de autoservicio que [[adr-20-authorization-lobby]] regla 3 cerró.
- **Una clase de permiso por combinación rol/área/método** — permisos hechos a medida por endpoint. Perdió contra las reglas 1 y 2: la matriz con `read_groups`/`write_groups` cubre el pedido sin multiplicar clases.

## RELATED

### related adrs

- [[docs/adrs/adr-20-authorization-lobby]] — reglas 2 y 3, el alcance de una sesión y cómo se otorga un rol
- [[docs/adrs/adr-10-auth]] — reglas 1–2, Cognito autentica y Django autoriza
- [[docs/adrs/adr-45-lot-owner-assistant-access]] — la tercera ruta que alcanza el portal
- [[docs/adrs/adr-25-account-ledger]] — regla 1, por qué no hay débito manual
- [[docs/adrs/adr-51-api-and-backend]] — regla 1, el gateo declarado en [[API]] antes del código

### related files

- [[docs/API]] — la columna Auth de cada ruta
- [[docs/AUTH]] — la sesión sobre la que se decide el rol
- [[docs/GLOSSARY]] — los nombres de los seis grupos
- [[docs/feedlot/09-usuarios-y-permisos]] — las funciones del campo que estos roles modelan
