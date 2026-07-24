# 12 · Especificación de frontend (fases 3-4-5)

> Plan de ejecución para el frontend, anclado en el sistema de diseño real del template (Astro SSR + islas Svelte, componentes UI estilo shadcn, i18n). Escrito para que en Claude Code sea **ejecutar**, no rediseñar. Gobernado por adr-04 (frontend y design system).

**Estado:** backend de las fases 3-4-5 en `main`. Frontend: no empezado.

## Convenciones del template (respetarlas al pie)

Verificadas leyendo el repo, no supuestas:

- **Páginas** en `src/pages/*.astro`, SSR (`output: "server"`). El fetch al backend se hace **en el server** con la cookie de sesión (`BACKEND_API_URL`), como en `profile.astro`. No se llama al backend desde el navegador salvo en islas.
- **Interactividad** en islas Svelte (`client:load`), no en el `.astro`.
- **Componentes UI** ya existen en `src/lib/components/ui/`: `card`, `table`, `badge`, `button`, `alert`, `input`, `label`, `separator`, `avatar`. **Usarlos**, no crear nuevos primitivos.
- **i18n obligatorio**: todo texto visible sale de `t("clave")`; las claves son snake_case inglés en `src/i18n/messages/es.ts`, el valor es el español. Nada de strings hardcodeados en español en los componentes (adr-01).
- **Auth**: cada página usa `requireRole(me)` y redirige si falta rol, como `profile.astro`. Las vistas del feedlot necesitan su grupo RBAC (ver abajo).
- **Cabecera LIVE-DOC** en cada archivo nuevo, con `Governed by: [[adr-04...]]`.
- **Tests**: `bun:test` únicamente, sin jsdom. Lógica de fetch/parseo en módulos DOM-free e inyectables (patrón `router-client.ts`), testeados aparte del render.

## Decisión pendiente que bloquea los gráficos

**[DECISIÓN] Librería de gráficos.** El template **no** trae ninguna (deps: astro, svelte, htmx, melt, tailwind). Hay que elegir antes de la Fase 3 visual:

| Opción | A favor | En contra |
|---|---|---|
| **LayerChart** (Svelte-native) | Encaja con Svelte 5, componible | Dependencia nueva |
| **Chart.js** (envuelto en isla) | Maduro, conocido | Imperativo, no idiomático en Svelte |
| **SVG a mano** (sin dep) | Cero dependencias, control total | Más trabajo por gráfico |

Propuesta: **LayerChart** para curvas y barras (crecimiento, costo diario, precios); SVG a mano solo si un gráfico puntual no encaja. Confirmar en Claude Code según lo que ya conozca el equipo.

## El contrato no negociable: manejar el `null`

Las métricas de la Fase 3 y los precios de la Fase 4 devuelven **`null` con `not_calculable`** cuando no hay dato honesto (adr-29). El frontend **debe** distinguir tres estados en cada tarjeta y cada gráfico:

1. **Dato** → se muestra.
2. **`null` + motivo** → se muestra un guion o "—" con el motivo en tooltip ("sin pesajes en el período", "sin ingresos en el período"). **Nunca un cero.**
3. **Cargando / error de fetch** → estado propio, no confundir con `null`.

Un componente `<Metric>` que reciba `{value, notCalculable}` y renderice los tres estados es la pieza que evita graficar ceros inventados. Hacerlo una vez y reusarlo.

## Páginas a construir

### Fase 3 — Dashboard por cliente · `src/pages/clientes/[id]/dashboard.astro`

SSR: trae `GET /api/clients/{id}/metrics/summary/` y lo pasa a las islas.

Bloques (cada uno una `Card`):

- **Encabezado de hacienda** — cabezas, kg totales, peso promedio (de `herd`). `average_weight` puede ser `null` (rodeo vacío) → estado 2.
- **Saldo** — `balance`, con signo explicado ("positivo = el cliente debe").
- **Desglose de costo** — barras por concepto (`cost.by_concept`): alimentación, sanidad, servicio, ajuste. Isla con el gráfico.
- **Conversión alimenticia** — número grande; si `conversion == null`, estado 2 con el motivo (`no_measured_growth` / `no_weight_gain`). **Este es el caso más frecuente de `null`** (ver 06c y el plan de fases): la UI tiene que hacerlo legible, no romperse.
- **Mortandad** — `dead_head / entered_head` y la tasa; `null` si no hubo ingresos.
- **Curva de cuenta** — serie de `GET .../metrics/account/`, línea del saldo corrido.
- **Curva de crecimiento** — `GET .../metrics/growth/`, con los tramos "no calculables" marcados visualmente (hueco, no cero).
- **Inconsistencias** — si `inconsistencies` trae algo, un `Alert` amarillo ("raciones cargadas después de la muerte del animal X").

### Fase 4 — Precios de hacienda · `src/pages/precios/index.astro`

SSR: `GET /api/market-prices/?source=canuelas` y `?source=ipcva`.

- **Tabla** por categoría (`Table` ui): mínimo, máximo, promedio, mediana, cabezas, con la fecha del dato y un `Badge` de la fuente.
- **Selector de fuente** — Cañuelas / IPCVA / manual. **No mezclar fuentes en una serie** (adr-30 regla 8): mostrar una por vez, o dos series distinguidas por color, nunca un promedio de ambas.
- **Formulario de carga manual** — isla que POSTea a `/api/market-prices/`. Es el respaldo cuando el scraper falla, así que tiene que estar cómodo de usar (adr-30), no escondido.
- **Aviso de frescura** — si el último precio de una fuente tiene varios días, un `Alert` ("Cañuelas sin actualizar desde el DD/MM"). Ata con el monitoreo del scraper.

### Fase 5 — Asesores · `src/pages/clientes/[id]/asesores.astro`

SSR: `GET /api/advisor-reports/?client={id}` (reportes ya generados).

- **Tres tarjetas**, una por asesor (ganadero, financiero, administrativo).
- **Botón "Generar informe"** — isla que POSTea a `/api/advisor-reports/` con `{advisor, client, start, end}`. Muestra spinner mientras infiere (es async, puede tardar).
- **Render del informe** — el `output` en prosa, con un desplegable "ver datos que vio el asesor" que muestra el `input_snapshot`. Esa transparencia es el punto del adr-27: la sugerencia se lee junto a los datos que la respaldan.
- **Descargo** — texto fijo: "Sugerencias generadas por IA sobre los datos del período; no son certezas". Requisito del adr-27 sobre márgenes de error.

## Módulos DOM-free a testear (patrón router-client.ts)

Extraer y testear con bun:test, sin render:

- `metrics-client.ts` — arma las URLs de métricas y tipa las respuestas **incluyendo el `null`**. Los tipos deben forzar al que consume a contemplar `not_calculable`.
- `market-client.ts` — fetch de precios + POST de carga manual.
- `advisors-client.ts` — fetch de reportes + POST de generación.

Tipar el `null` en el TypeScript es lo que hace que un dashboard que asuma "siempre hay número" **no compile**, en vez de romper en producción.

## RBAC

Las vistas del feedlot necesitan su grupo (adr-10). Propuesta de grupos Django: `feedlot_operators` (carga y ve), `feedlot_viewers` (solo ve), `feedlot_admin` (todo + carga manual de precios). Definir con el guardián de auth; el `requireRole` de cada página los consume.

## Orden sugerido

1. Componente `<Metric>` (los tres estados) + `metrics-client.ts` con sus tests.
2. Dashboard (Fase 3) — es el que valida el contrato del `null`.
3. Precios (Fase 4) — reusa `<Metric>` y la tabla.
4. Asesores (Fase 5) — el más simple en UI, depende de que el POST async ande.

Cada página entra por el flujo del repo (issue → worktree → PR) y suma sus filas a `API.md` y sus claves a `es.ts` antes del código.
