# 07 · Arquitectura escalable y roadmap

## El principio: se crece por adición

El repositorio base tiene una regla de oro: **una capacidad nueva es una app de dominio nueva; la base no se toca**. El feedlot adopta ese principio para poder sumar rubros del campo mañana sin reescribir nada.

La clave está en separar **la columna vertebral compartida** de **los rubros**:

```
COLUMNA VERTEBRAL (compartida, estable)
  clients   → clientes y cuentas
  ledger    → cuenta corriente (cobra cualquier cosa, de cualquier rubro)
  market    → precios de referencia
  advisors  → asesores con IA

RUBROS (se suman de a uno)
  livestock + feed + health   → ganadería (hoy)
  equines                     → caballos (mañana)
  crops                       → alfalfa, círculos de riego (mañana)
  machinery + workshop        → maquinaria, taller, mantenimiento (mañana)
```

La pieza que lo hace posible es el **costeo genérico**: cualquier evento de cualquier rubro puede postear un cargo a la cuenta de un cliente referenciándose con un par (`source_kind`, `source_id`), sin que el `ledger` necesite conocer al rubro. Una tarea de alfalfa, un service de maquinaria o una ración de hacienda entran al libro por la misma puerta.

## Cómo sería un rubro nuevo

Cada rubro nuevo aporta:

- Sus **entidades** (p. ej. para alfalfa: `Pivot`/círculo, con tamaño y ubicación; `Crop`/siembra con su ciclo; `FieldTask`/tarea con su costo; pesajes o cortes).
- Sus **eventos operativos** inmutables (siembra, riego, corte, tarea, cosecha).
- El **posteo de costos** al `ledger` cuando corresponde.
- Opcionalmente, un **asesor** especializado (o se reutilizan los existentes con contexto del rubro).

Ideas ya conversadas, para tener presentes al diseñar la columna:

- **Caballos (`equines`):** individuos con identificación, sanidad, alimentación, servicios. Muy parecido a `livestock` en forma; puede reutilizar patrones de animal/sanidad.
- **Alfalfa y pivotes (`crops`):** cargar los círculos (tamaño), su crecimiento/cortes, tareas y costos. Introduce el par genérico `Asset` (el pivote/parcela) + `Task` (la labor).
- **Taller y maquinaria (`machinery`, `workshop`):** activos con **ciclo de vida** y **mantenimiento**. Sugiere un patrón genérico `Asset` + `MaintenanceEvent` (service, repuesto, horas de uso) que también sirve a otros rubros.

Un par de conceptos genéricos —`Asset`, `Task`, `MaintenanceEvent`— aparecen en más de un rubro. Cuando lleguemos a ellos, conviene sacarlos a una app compartida (`assets`) en vez de repetirlos. No se construyen ahora; se dejan anotados para no pintarnos a una esquina.

## Roadmap por fases

Cada fase es entregable y usable por sí sola. El orden prioriza poder **operar y cobrar** cuanto antes.

### Fase 0 — Documentación (esta)
Visión, modelo de datos, módulos, dashboard, asesores, precios y escalabilidad, en este Proyecto y en formato del repo. **Estado: en curso.**

### Fase 1 — Núcleo operativo
- `clients` + `ledger`: clientes, cuentas, movimientos y pagos.
- `livestock` (ingreso): alta de hacienda individual y por lote.
- `feed`: catálogo, stock propio y por cliente, entregas del cliente, y la **carga de raciones con costeo** (la regla propio/cliente).
- Resultado: se puede operar el día a día y ver el saldo de cada cliente.

### Fase 2 — Ciclo del animal
- Pesajes y crecimiento (GDP, peso promedio).
- Muertes y salidas (individual y parcial de lote).
- `health`: sanidad con costeo.
- Resultado: trazabilidad completa del ciclo y todos los cargos automáticos.

### Fase 3 — Dashboard y métricas
- Tablero por cliente: indicadores, curvas, costeo diario, conversión, mortandad, evolución de cuenta.
- Resultado: lectura de gestión por cliente.

### Fase 4 — Precios de hacienda
- `market`: fuentes, ingesta automática (CKAN datos.gob.ar) + scraping (Cañuelas) + manual.
- Resultado: referencia de mercado en métricas y para el asesor financiero.

### Fase 5 — Asesores IA
- `advisors`: los tres perfiles sobre datos del cliente, con informes auditables.
- Resultado: recomendaciones ganaderas, financieras y administrativas.

### Fase 6+ — Multi-rubro
- Extraer `assets`/`tasks` genéricos y sumar rubros (caballos, alfalfa, taller, maquinaria) de a uno.
- Resultado: el sistema deja de ser "de feedlot" y pasa a ser "del campo".

## Cómo se construye cada pieza (método del repo)

El repositorio impone un flujo por el que conviene pasar cada feature: la idea se documenta, si toca backend entra por el archivo `API` (la única fuente de endpoints válidos), se escribe con TDD (test primero), y el cambio va por *issue → worktree → PR*. No hace falta seguirlo al pie de la letra en esta etapa de diseño, pero sí al empezar a codear: por eso, además de estos documentos, se preparan los archivos en el **formato del repo** (ADRs, glosario, filas de API propuestas) listos para entrar por ese flujo. Ver el paquete entregado junto a esta documentación.
