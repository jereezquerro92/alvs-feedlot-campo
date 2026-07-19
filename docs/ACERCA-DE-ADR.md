---
created: '2026-07-15'
tags:
- adr
- resumen
- personal
title: Acerca de ADR
type: note
---

Resumen personal, un párrafo muy corto por ADR, en castellano y sin links — para repasar rápido qué hace cada una sin tener que abrirlas todas.

## ADR-00 — doctrina de ADRs (superada)

Vacía: quedó reemplazada por la ADR-19 y no aporta contenido.

## ADR-01 — glosario y localización

Obliga a que todo nombre técnico se registre antes en el glosario, y a que el código sea siempre en inglés; el español solo puede aparecer en lo que el usuario final ve.

## ADR-02 — stack inicial

Fija que solo se usa lo que está pinneado en REQUIREMENTS, con uv y bun como únicas herramientas, y la infraestructura como dos servicios Fargate en AWS.

## ADR-03 — API y backend

Dice que ningún endpoint puede existir en código si antes no tiene su fila en API.md, y ordena el camino: primero API, después tests, después modelos.

## ADR-04 — frontend y design system

Define Astro con islas Svelte, obliga a escalar de HTML a HTMX y recién después a Svelte, y separa estrictamente qué es página y qué es componente.

## ADR-05 — HTMX

Establece que los fragmentos HTML los genera Django, que Astro solo los engancha, y que cada fragmento es un endpoint declarado como cualquier otro.

## ADR-06 — cache

Prohíbe para siempre cualquier servidor de cache tipo Redis y reduce toda la estrategia a cuatro capas explícitas, con cabeceras de cache siempre presentes.

## ADR-07 — flujo de desarrollo

Marca el loop obligatorio de todo feature: primero una historia BDD, después pasar por API antes de tocar backend, y volver al frontend recién cuando API alcanza.

## ADR-08 — GitHub y git

Fija que main es integración y prod es producción, que solo kodexArg pushea a esas ramas, y cómo se nombran tags y labels.

## ADR-09 — docker-compose

Reserva backend/ y frontend/ como únicos lugares para el código de las apps, y fija un solo compose.yaml en la raíz para orquestar todo localmente.

## ADR-10 — autenticación

Establece que Cognito solo autentica y nunca autoriza, que los roles viven exclusivamente en Django Groups, y define la única cuenta con password permitida.

## ADR-11 — agentes guardianes

Crea tres agentes que vigilan PRD, las ADRs y API respectivamente, y los vuelve el gate obligatorio para cualquier cambio que toque esos documentos.

## ADR-12 — corrida efímera de referencia

Declara que toda la infraestructura de este despliegue de referencia nace para ser destruida, con inventario y tags que gobiernan ese teardown.

## ADR-13 — Microsoft Graph app-only

Habilita Graph como capa de capacidad sin login humano — credenciales de aplicación —, nunca como un segundo proveedor de identidad.

## ADR-14 — harness de skills

Exige que cada skill requerida esté vendida como copia real dentro del repo, sin depender de ningún harness global de la máquina.

## ADR-15 — chatbot de dos niveles

Separa para siempre un nivel que elige de un menú cerrado con poder de acción, de un nivel que solo genera texto y nunca puede accionar nada.

## ADR-16 — async obligatorio como capacidad

Exige que el proyecto pueda volverse asíncrono cuando haga falta, sin forzar que cada vista lo sea por default.

## ADR-17 — live-doc en el código

Obliga a que cada archivo de código lleve un bloque de wikilinks que lo ata a las ADRs que lo gobiernan, generado automáticamente.

## ADR-18 — MCP de markdown-vault

Vuelve a ese MCP la puerta obligatoria para leer docs/, antes que cualquier Grep o Read directo.

## ADR-19 — doctrina de ADRs

Fija las reglas de forma de toda ADR: solo reglas, nunca información, y el mecanismo de supersesión cuando una regla cambia de sentido.

## ADR-20 — el lobby de autorización

Confina a cualquier sesión autenticada sin rol a la ruta / hasta que un admin le asigne un grupo en Django.

## ADR-21 — allowlist de bootstrap

Permite una lista por variable de entorno que pre-asigna rol a ciertas cuentas en su primer login, sin saltarse el mecanismo normal de grants.

## ADR-22 — componentes listos para showcase

Obliga a que todo componente de frontend funcione sin props y nunca dispare una acción que modifique datos por defecto.