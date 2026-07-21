# 04 · Dashboard y métricas

Un tablero **por cliente** que convierte los eventos registrados en indicadores y gráficos. Todo lo que muestra se **deriva** de los datos operativos; el dashboard no guarda números propios.

## Indicadores (tarjetas)

Vista rápida del estado de un cliente:

- **Hacienda actual:** cabezas activas y kilos totales (suma de animales + lotes activos).
- **Saldo de cuenta:** cuánto debe (o tiene a favor), con color según estado — se usan los tokens financieros que el repo ya trae (`--success` a favor, `--warning` neutro, `--negative` en rojo).
- **Costeo de alimentación del día / mes:** valorización de todo lo consumido (propio + del cliente), en ARS.
- **GDP promedio:** ganancia diaria de peso del período.
- **Conversión:** kg de alimento por kg ganado.
- **Mortandad:** cabezas muertas y % sobre ingresadas.

## Gráficos

| Gráfico | Qué muestra | De dónde sale |
|---|---|---|
| **Curva de crecimiento** | peso promedio del lote/animal en el tiempo | `Weighing` |
| **Ganancia diaria (GDP)** | kg/día por período, tendencia | `Weighing` (derivado) |
| **Costeo diario de alimentación** | ARS/día consumidos, apilado por origen (propio vs cliente) | `FeedingEvent` valorizado |
| **Consumo vs pesaje (conversión)** | cruce kg alimento contra kg ganados | `FeedingEvent` + `Weighing` |
| **Composición del alimento** | mezcla de tipos de alimento servidos | `FeedingEvent` por `FeedType` |
| **Mortandad** | muertes acumuladas / tasa en el tiempo | `Death` |
| **Evolución de la cuenta** | saldo y movimientos acumulados | `LedgerEntry` |
| **Referencia de mercado** | precio de hacienda vs. costo acumulado por animal | `MarketPrice` (ver módulo 06) |

## El cruce que importa

El valor del feedlot está en **cruzar consumo contra crecimiento**: cuánto comió el lote (y cuánto costó, propio o del cliente) contra cuánto engordó en el mismo período. De ahí sale la **conversión alimenticia** y, contra el **precio de hacienda** de referencia, una lectura de rentabilidad: cuánto cuesta poner un kilo encima vs. cuánto vale ese kilo en el mercado. Ese cruce es también el insumo principal de los [asesores](05-asesores-ia.md).

## Cómo se calcula (rendimiento)

Los indicadores son agregaciones sobre tablas de eventos que pueden crecer mucho. Criterio:

- **Fase 3 (MVP del dashboard):** agregaciones en vivo con consultas SQL sobre los eventos (índices adecuados por `client` + `date`). Suficiente para el volumen inicial.
- **Cuando escale:** tablas de resumen diario pre-calculadas (p. ej. `DailyClientMetric`: consumo, costo, cabezas, kg, muertes por cliente y día), actualizadas por un job. El dashboard lee el resumen; el detalle sigue disponible en los eventos. Se decide cuando el volumen lo pida, no antes.

## Frontend

Se sirve como página Astro SSR con islas Svelte para lo interactivo (filtros de fecha, selector de cliente/lote) y fragmentos HTMX para las tablas de detalle, siguiendo el sistema de diseño del repo. Persistible como artefacto/tablero para que el equipo lo abra recurrentemente.

> **[DECISIÓN] — Biblioteca de gráficos.**
> El repo aún no tiene una. Opciones a evaluar en Fase 3: una librería liviana compatible con Svelte (p. ej. LayerChart, que encaja con el ecosistema, o Chart.js embebido en una isla), o gráficos SVG renderizados en servidor para las vistas más simples. Se define al empezar el dashboard, respetando `REQUIREMENTS` del repo.
