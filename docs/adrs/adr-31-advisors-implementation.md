---
title: adr-31-advisors-implementation
type: adr
category: backend
use_case: generar un informe de asesor, armar o cambiar el snapshot, elegir el cliente de inferencia, testear la generación sin red
created: 2026-07-23
modified: 2026-08-02
tags: [adr, feedlot, advisors, inference, bedrock, phase-5]
---

# ADR-31 — Implementación de los asesores

## CONTEXT

> Cómo se construyeron los asesores que [[adr-27-advisors-generative]] fijó. La pieza delicada no es la generación —pedirle texto a un modelo es fácil— sino garantizar que ese texto sea auditable y acotado a un cliente.

## ASSERTIONS

1. `apps.advisors.snapshot.build_snapshot` es el único punto que toca la base de un cliente. El asesor recibe un dict y nada más: adentro no hay camino hacia la base ni hacia otro cliente ([[adr-27-advisors-generative]] regla 2).
2. `generate_report` arma el snapshot con el `client` que se le pasa y no acepta uno armado desde afuera, de modo que un llamador no puede colar datos de otro cliente. El scope por cliente es una barrera dura, no una convención.
3. El snapshot se arma desde `apps.metrics` ([[adr-29-metrics-derivation]]): el asesor y el gráfico que ve el cliente leen los mismos números y no pueden contradecirse. Si la conversión sale "no calculable" en el dashboard, sale igual para el asesor.
4. `AdvisorBedrockClient` (real) y `MockAdvisorClient` (determinista) se eligen en `get_advisor_client`, único punto de selección, gateado por DEBUG igual que el router ([[adr-15-chatbot-two-tier]]). Un proceso no-DEBUG sólo puede construir el cliente real; ningún setting fuerza el mock a un deploy. A diferencia del router, este tier genera prosa: temperatura 0.3.
5. Cada generación persiste un `AdvisorReport` con snapshot, output, `model_id`, tokens y latencia; leer un reporte no vuelve a inferir ([[adr-27-advisors-generative]] regla 3). Eso es lo que hace auditable una sugerencia económica: se ve exactamente qué datos vio el modelo.
6. La inferencia real necesita `ADVISOR_BEDROCK_MODEL_ID` y la región en [[VARIABLES]], el permiso IAM, el gate de conectividad Bedrock y el envoltorio async de [[adr-16-async-mandatory]] regla 4 (`sync_to_async`, nunca `aiobotocore`). Los tests corren contra el mock.
7. La generación es a demanda o programada: el `POST` dispara una y ninguna señal genera sola. Los viewsets exponen `list`/`retrieve`/`create` de reportes y jamás una mutación de datos del cliente. Un asesor inactivo rechaza la generación en el servicio, no en la vista.

## FORBIDDEN

- **NEVER** aceptar un snapshot armado por el llamador (regla 2). Es la vía por la que los datos de otro cliente entran al paquete sin que nada lo note.
- **NEVER** darle al asesor un camino a la base (regla 1). El snapshot es todo lo que ve, y por eso la barrera se verifica en un solo lugar.
- **NEVER** seleccionar el cliente de inferencia fuera de `get_advisor_client` (regla 4). Dos puntos de selección son dos políticas, y una de las dos se olvida del gate.
- **NEVER** permitir que un setting fuerce el mock fuera de DEBUG (regla 4). Un deploy que responde con texto determinista parece funcionar.
- **NEVER** re-inferir al leer un reporte (regla 5). El registro dejaría de ser el registro.
- **NEVER** usar `aiobotocore` para la inferencia (regla 6). [[adr-16-async-mandatory]] regla 4 fija `boto3` envuelto en `sync_to_async`.

## REJECTED

- **Recibir el snapshot como parámetro del endpoint** — dejar que el caller arme el paquete y el servicio sólo infiera. Rechazado por la regla 2: haría del aislamiento entre clientes una convención del llamador.
- **Definir las métricas del snapshot dentro de `advisors`** — fórmulas propias del asesor, ajustadas a lo que le sirve narrar. Rechazado por la regla 3; el asesor y el dashboard tienen que poder contradecirse sólo si los hechos cambian.
- **Temperatura 0 como en el router** — la misma configuración del tier que elige. No aplica: este tier genera prosa, y es la excepción generativa acotada de [[adr-27-advisors-generative]].

## RELATED

### related adrs

- [[docs/adrs/adr-27-advisors-generative]] — las reglas que este ADR implementa
- [[docs/adrs/adr-29-metrics-derivation]] — la única definición de cada número del snapshot
- [[docs/adrs/adr-15-chatbot-two-tier]] — el patrón de cliente de inferencia que la regla 4 calca
- [[docs/adrs/adr-16-async-mandatory]] — regla 4, cómo se llama a Bedrock
- [[docs/adrs/adr-35-conversational-assistant]] — el mismo patrón, en el asistente

### related files

- [[docs/VARIABLES]] — `ADVISOR_BEDROCK_MODEL_ID` y la región
- [[docs/FEEDLOT-DATA-MODEL]] — `Advisor` y `AdvisorReport`
- [[docs/API]] — las rutas de asesores
