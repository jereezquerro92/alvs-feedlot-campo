# ADR-31 — Implementación de los asesores

**Estado:** propuesto (Fase 5)
**Contexto:** implementa [[adr-27-advisors-generative]]; reusa el patrón de [[adr-15-chatbot-two-tier]] (inference clients) y respeta [[adr-16-async-mandatory]].

## Contexto

El ADR-27 fijó las reglas de los asesores; esto es cómo se construyeron. La pieza
delicada no es la generación —es fácil pedirle texto a un modelo— sino garantizar
que ese texto sea **auditable y acotado a un cliente**.

## Decisiones

### 1. El snapshot es lo único que lee datos

`apps.advisors.snapshot.build_snapshot` es el único punto que toca la base de un
cliente. El asesor recibe un dict y nada más. No hay, dentro del asesor, ningún
camino hacia la base ni hacia otro cliente (adr-27 regla 2).

### 2. El snapshot se arma en el servicio, no se recibe

`generate_report` construye el snapshot con el `client` que se le pasa; no acepta
un snapshot armado desde afuera. Así un llamador no puede colar datos de otro
cliente en el paquete. El scope por cliente es una barrera dura, no una convención.

### 3. Una sola definición de cada métrica

El snapshot se arma desde `apps.metrics` (Fase 3). El asesor y el gráfico que ve
el cliente leen los mismos números — no pueden contradecirse porque son la misma
fuente. Si la conversión sale "no calculable" en el dashboard, sale igual para el
asesor.

### 4. Cliente de inferencia calcado del router

`AdvisorBedrockClient` (real) y `MockAdvisorClient` (determinista) con
`get_advisor_client` como único punto de selección, gateado por DEBUG igual que el
router (adr-15). Un proceso no-DEBUG solo puede construir el cliente real; ningún
setting fuerza el mock a un deploy. Diferencia con el router: este tier **genera
prosa** (temperatura 0.3, no 0) — es la excepción generativa acotada del adr-27.

### 5. El reporte es el registro

Cada generación persiste un `AdvisorReport` con snapshot, output, model_id, tokens
y latencia. Leer un reporte **no** vuelve a inferir (adr-27 regla 3). Esto es lo
que hace auditable una sugerencia económica: se puede ver exactamente qué datos vio
el modelo.

## Punto de integración pendiente (Claude Code, contra AWS)

`AdvisorBedrockClient` sigue el patrón del router pero necesita, contra AWS real:
el `ADVISOR_BEDROCK_MODEL_ID` y la región en `VARIABLES`, el permiso IAM, el gate
de conectividad Bedrock (como `bedrock_live` del router), y el envoltorio async
(adr-16 regla 4: `sync_to_async`, nunca `aiobotocore`). Los tests corren contra
`MockAdvisorClient`, igual que el router prueba su tier con su propio mock.

## Consecuencias

- La generación es a demanda o programada, nunca en cada escritura de datos
  (adr-27 regla 4). El endpoint POST dispara una; no hay señal que genere sola.
- El asesor es read-only: los viewsets exponen list/retrieve/create de reportes,
  jamás una mutación de datos del cliente.
- Un asesor inactivo rechaza la generación en el servicio, no en la vista.
