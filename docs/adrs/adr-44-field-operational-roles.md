---
title: ADR-44 — Los seis roles operativos del campo y el scoping por cliente
type: adr
status: active
created: 2026-07-27
tags: [adr, rbac, auth, roles, feedlot]
---

# ADR-44 — Los seis roles operativos del campo y el scoping por cliente

**Contexto:** amplía [[adr-20-authorization-lobby]] regla 2 (agregar un alcance de rol
o ampliar qué rutas alcanza una sesión exige un ADR nuevo, nunca una excepción local)
y reusa el precedente de grupo-por-concern de [[adr-11-guardians]] y el par
`AccessRequest` + señal `post_save` de [[adr-20-authorization-lobby]] regla 3. No
supersede nada: Cognito sigue autenticando y los Django Groups siguen siendo la única
autoridad de RBAC ([[adr-10-auth]] reglas 1–2, intactas). Reglas solamente; los nombres
entran en [[GLOSSARY]] antes de su primer uso ([[adr-01-glossary-and-localization]]).

## Contexto

El template dejó dos grupos: `admins` (superset) y `ai_operators` (solo router). El
dueño pidió los roles reales del campo: seis funciones distintas, cada una con su
recorte de lo que puede ver y cargar. Uno de ellos —los dueños de lotes— es un
**portal de cliente**: ve datos de UN cliente y de ningún otro. Ese recorte es una
frontera de aislamiento entre inquilinos, no una comodidad de UI, y por eso se decide y
se enforcea en el backend.

## Los seis roles (grupos Django)

| Rol (negocio) | Grupo Django | Naturaleza |
|---|---|---|
| Encargado del campo | `field_managers` | staff; ve todo lo operativo; carga deudas (cuentas) |
| Operativo (mixer) | `feed_operators` | staff; prepara el mixer (órdenes de carga, feeding, lectura de comedero) |
| Dueños de lotes | `lot_owners` | portal de cliente; **read-only**; acotado a SU cliente |
| Administrativo del campo | `field_admins` | staff; carga ingresos de mercadería a stocks (campo y propios por contrato) |
| Dueño del campo | `feedlot_owners` | staff/dueño; **read** sobre todos los clientes (hacienda por contrato y propia) |
| Usuarios de taller | `workshop` | staff; carga maquinaria, mantenimiento, combustible, alfalfa (cultivos) |

`admins` conserva el superset: puede todo, es aceptado por toda clase de permiso
(cortocircuito en la clase base). `ai_operators` sigue siendo solo del router y no se
agrega a ninguna otra clase ([[adr-11-guardians]], [[GLOSSARY]]).

## Decisiones

### 1. Un rol es un Django Group; la matriz vive en un solo archivo

Cada rol es un `auth.Group` creado por migración (mismo patrón que `admins`,
[[adr-10-auth]]). La autorización se decide por membresía de Group, leída en Django,
nunca en un claim de Cognito ([[adr-10-auth]] regla 2). Toda la matriz rol→área→método
vive centralizada en `apps/users/roles.py` (`GroupMatrixPermission` con `read_groups` /
`write_groups` por área funcional); un viewset solo referencia su clase de área. Ajustar
quién puede qué es editar ese único archivo, no cazar permisos por cada app.

*Por qué:* una matriz dispersa por 50 viewsets se desincroniza. Centralizarla la hace
auditable de un vistazo y barata de corregir cuando el dueño la afina.

### 2. `read`/`write` se separan por método HTTP dentro de cada área

`GroupMatrixPermission` acepta métodos seguros (GET/HEAD/OPTIONS) si el usuario está en
`read_groups` y métodos de escritura (POST/PUT/PATCH/DELETE) si está en `write_groups`.
`admins` pasa siempre. Un rol puede leer un área sin poder escribirla (p.ej. el dueño
del campo lee stocks pero no los carga).

*Por qué:* casi todos los roles son "ver esto, cargar aquello". Modelar lectura y
escritura como conjuntos separados por área cubre el pedido sin una clase por
combinación.

### 3. Los dueños de lotes se confinan a una superficie por-cliente, gateada por el `client_id` de la ruta

`lot_owners` es **read-only** y su alcance es exactamente las rutas keyed por un cliente:
las métricas (`/api/metrics/{client_id}/…`) y la cuenta del cliente
(`/api/clients/{id}/account|ledger|outstanding`). `ClientScopedReadPermission` compara el
`client_id`/`pk` de la ruta contra el cliente ligado a la sesión
(`AccessRequest.client`, decisión 4) y **rechaza (404/403) si no coincide**. No se les
expone la lista cruda de animales/feedings/etc.: ven **métricas agregadas de sus vacas y
su saldo** —exactamente lo pedido— y ninguna tabla que pudiera mezclar clientes.

*Por qué:* aislar por queryset a través de ~15 modelos (cada uno con su camino al
cliente) es donde un solo error filtra datos de otro inquilino. Confinar el portal a las
rutas ya keyed por `client_id` reduce la superficie a **una** comparación, testeable y
sin ambigüedad. Un cero de exposición por defecto es preferible a un filtro amplio y
frágil.

### 4. El vínculo usuario→cliente es un campo en `AccessRequest`, puesto por un admin

`AccessRequest` gana un FK nullable `client` → `clients.Client`. Lo setea un admin en
`/admin/` (misma postura que [[adr-20-authorization-lobby]] regla 3: un grant es acción
de admin, jamás autoservicio). Un `lot_owners` sin `client` ligado no ve **ningún**
cliente —falla cerrado—, nunca "todos por defecto". El campo no otorga autoridad por sí
mismo: la membresía al grupo `lot_owners` es lo que activa el scoping; `client` solo dice
*cuál*.

*Por qué:* reusa la maquinaria de grants existente y mantiene la decisión de acceso en
Django y en manos de un admin. Fallar cerrado ante un vínculo faltante es la única opción
segura para una frontera entre inquilinos.

### 5. El dueño del campo y el encargado ven todos los clientes; no se scopean

`feedlot_owners` y `field_managers` (y `admins`) leen sin recorte por cliente: el pedido
del dueño del campo es agregar "cuántos animales tengo, por contrato y propios", que es
una vista cross-cliente. El scoping por cliente de la decisión 3 aplica **solo** a
`lot_owners`.

*Por qué:* son roles internos del feedlot, no inquilinos. Recortarlos por cliente
contradiría su función.

### 6. "Carga de deudas" del encargado son eventos y pagos, no un débito manual

El ledger es event-sourced e inmutable ([[adr-25-account-ledger]] regla 1): no existe un
endpoint de "débito manual". "Cargar deudas en cuentas corrientes" se cumple con lo que
ya postea al ledger —eventos que cobran (feeding de stock propio, sanidad) y `Payment`
(crédito)— todos escribibles por `field_managers`. Un endpoint de ajuste manual, si el
negocio lo pide, entra como su propio cambio por [[API]] y [[adr-07-development-flow]],
nunca mutando un asiento.

*Por qué:* honramos la doctrina del ledger. La comodidad de un débito arbitrario no
justifica abrir una escritura directa al asiento que [[adr-25-account-ledger]] cerró.

### 7. Todo endpoint feedlot declara su clase de permiso en [[API]] antes del código

La columna Auth de [[API]] deja de decir `session` genérico para las rutas gateadas: dice
la clase de permiso (y por lo tanto los grupos) que las protege
([[adr-03-api-and-backend]] regla 1). Cambiar el gateo de una ruta es cambiar su fila
primero.

*Por qué:* [[API]] es el SSOT del contrato de rutas; el gateo es parte del contrato.

## Consecuencias

- El backend entra solo por [[API]] ([[adr-03-api-and-backend]]) y nace por el flujo
  [[TDD]] ([[adr-07-development-flow]]); este ADR no exceptúa ese camino.
- Migraciones: una crea los seis grupos; otra agrega `AccessRequest.client`. Ningún
  modelo de dominio se refactoriza —la extracción mira hacia adelante
  ([[adr-32-multi-rubro-assets]] regla 2).
- `/api/me/` gana el cliente ligado (id + nombre) para que el frontend scopee la UI; el
  backend sigue siendo la frontera de seguridad, el frontend es solo UX.
- El frontend gatea navegación y rutas por `me.groups` y usa `me.client` para el portal
  del dueño de lote; ese gateo es conveniencia, no la barrera (la barrera es el backend).
- La matriz de la decisión 1 es una superficie de iteración pre-v1: el dueño la afina
  editando `roles.py` y esta tabla; cambios de las reglas 1–7 son semánticos y DEBEN
  superseder este ADR ([[adr-00-adr-doctrine]] regla 4).
