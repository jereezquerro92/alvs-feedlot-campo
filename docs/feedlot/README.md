# ALVS — Feedlot Campo · Documentación maestra

> Sistema de trazabilidad para feedlot: hacienda propia + hotelería de vacas de clientes, con costeo de alimentación, sanidad y servicios en cuenta corriente, dashboards por cliente, asesores con IA, control de accesos multiusuario y arquitectura escalable a otros rubros del campo.

**Estado:** diseño / documentación (previo a código).
**Última actualización:** 2026-07-21.
**Repositorio base:** [kodexArg/astro-drf-aws](https://github.com/kodexArg/astro-drf-aws) — Astro 7 SSR + Svelte + Tailwind 4 (frontend), Django 6 + DRF (backend), AWS Fargate + RDS PostgreSQL, con autenticación Cognito/OIDC ya resuelta.

## Cómo leer esta documentación

Esta carpeta es la fuente de verdad del **negocio y el diseño**. El código se escribe después, siguiendo el "harness" del repo (PRD → ADRs → API → docs). Cada documento cubre un tema y evita repetir lo que ya vive en otro.

| # | Documento | Qué contiene |
|---|-----------|--------------|
| 01 | [Visión, alcance y glosario](01-vision-alcance-glosario.md) | Para qué existe el sistema, qué entra y qué no en cada fase, y el vocabulario canónico del dominio. |
| 02 | [Modelo de datos](02-modelo-de-datos.md) | Entidades, campos, relaciones y el diagrama del esquema. La columna vertebral. |
| 03 | [Módulos operativos y reglas de negocio](03-modulos-operativos.md) | Alimentación + stock, animales/lotes, sanidad, cuenta corriente y pagos. Las reglas finas (origen del alimento, costeo, muertes, salidas). |
| 04 | [Dashboard y métricas](04-dashboard-metricas.md) | Tablero por cliente, indicadores, cruces (consumo vs pesaje) y gráficos. |
| 05 | [Asesores con IA](05-asesores-ia.md) | Los tres asesores (ganadero, contable-financiero, administrativo) y cómo se construyen sobre los datos del cliente. |
| 06 | [Precios de hacienda](06-precios-hacienda.md) | Fuentes argentinas de precios de referencia, cuáles se pueden automatizar y estrategia de ingesta. |
| 07 | [Arquitectura escalable y roadmap](07-arquitectura-escalable-y-roadmap.md) | Cómo se suman rubros nuevos (caballos, alfalfa, taller, maquinaria) sin romper lo hecho, y el plan por fases. |
| 08 | [Costos y servicios](08-costos-y-servicios.md) | Mano de obra, maquinaria, combustible, fletes y servicios: cómo se cargan a la cuenta del cliente. |
| 09 | [Usuarios y permisos](09-usuarios-y-permisos.md) | Multiusuario con permisos granulares y escalables; perfiles propuestos por los asesores. |

## Resumen ejecutivo

El sistema resuelve cuatro cosas al mismo tiempo:

1. **Operación diaria trazable.** Cada día se registra qué comió cada lote o animal, de qué tipo, cuánto peso, a qué precio del momento y de qué origen (alimento propio del feedlot o aportado por el cliente). Se registran ingresos de animales (individuales con caravana, o por lote con kilos totales), pesajes, muertes, salidas y sanidad.

2. **Costeo integral en cuenta corriente.** Todo lo que se le da al animal usando insumos del feedlot —alimento propio, sanidad, y **servicios como mano de obra, maquinaria, combustible y fletes**— se cobra a la cuenta del cliente en pesos, al valor del día. Los pagos compensan el saldo. La cuenta es un libro de movimientos inmutable.

3. **Inteligencia sobre los datos.** Dashboards por cliente (costeo diario, curvas de crecimiento, conversión, muertes, saldo, desglose de costos), precios de hacienda de referencia y tres asesores con IA.

4. **Control de accesos multiusuario.** Permisos granulares por acción (cargar datos, visualizar, cargar pagos, mantenimiento…), agrupados en perfiles que escalan con el proyecto, y que los asesores pueden proponer para cada persona.

La arquitectura sigue el principio del repositorio base: **se crece por adición**. Cada rubro nuevo del campo (caballos, alfalfa y pivotes de riego, taller mecánico, maquinaria) es una aplicación de dominio nueva que se apoya en la misma columna vertebral —clientes, cuenta corriente, precios, asesores y permisos— sin tocar lo ya construido.

## Decisiones ya tomadas

- **Unidad de la cuenta corriente:** pesos argentinos (ARS) con precio histórico capturado al momento de cada movimiento. Los precios de hacienda se usan como referencia para métricas, no como moneda de la cuenta.
- **Alcance de esta tanda:** documento maestro completo + maqueta visual navegable.
- **Dónde vive la documentación:** en este Proyecto de Claude (persistente, visible para el equipo) y, en paralelo, en archivos con el formato del repo listos para commitear.

## Decisiones abiertas (a confirmar)

Marcadas a lo largo de los documentos con **[DECISIÓN]**. Las principales:

- Si el alimento propio se cobra a costo o con margen, y qué pasa cuando se agota el stock aportado por el cliente.
- Prorrateo de costos generales (mano de obra, combustible del feedlot) entre clientes vs. carga directa.
- Alcance por cliente/establecimiento en los permisos (permiso a nivel de objeto): desde cuándo lo necesitamos.
- Si se lleva, además del ARS, un equivalente informativo en kilos de novillo.
- Biblioteca de gráficos del frontend (se define en la fase de dashboard).
