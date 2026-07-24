# 06c · Segunda fuente automática de precios (evaluación)

> Continúa [06b · Verificación de fuentes](06b-verificacion-fuentes-precios.md). Cierra la decisión abierta: qué fuente automática sumar junto a Cañuelas para no depender de un único origen.

**Fecha:** 2026-07-23.

## Veredicto: IPCVA (subdominio de estadísticas), no ROSGAN

Se evaluaron las dos candidatas que el documento 06 dejó como "complementarias". Resultado:

| Fuente | Sirve para segunda fuente automática | Motivo |
|---|---|---|
| **IPCVA** (`ipcva.agrositio.com`) | **Sí** | Páginas PHP renderizadas en servidor, con tablas de precios reales. Scrapeable sin navegador. |
| **ROSGAN** | **No** (como redundancia diaria) | La página de precios se arma con JavaScript; el HTML crudo viene vacío. Los datos son de remates (periódicos), no un precio diario por categoría. |

## IPCVA — segunda fuente elegida

El subdominio `ipcva.agrositio.com` expone vistas servidas por el servidor (PHP), no por el navegador, así que se pueden parsear con el mismo enfoque que Cañuelas. Las relevantes:

| Vista | URL | Qué da |
|---|---|---|
| Precios en Pie | `/estadisticas/vista_precios2.php?id=1` | Precio de hacienda en pie — **la más relevante** |
| Precios al Gancho | `/estadisticas/vista_precios2.php?id=2` | Precio de la res |
| Informe Mensual de Precios | `/vertodas2.php?se=84` | Serie mensual (también en PDF) |
| Precios al Consumidor | `/estadisticas/vista_precios_consumidor2.php` | Precio en góndola |

**Por qué es buena redundancia:** es un proveedor distinto de Cañuelas (el IPCVA agrega datos de varios mercados, no de uno solo), así que una falla del sitio de Cañuelas no arrastra a esta. Y al ser server-rendered, el conector es del mismo tipo que ya vamos a escribir.

**La limitación honesta:** el fuerte del IPCVA es la serie **mensual**, no el precio diario. Como redundancia del dato diario de Cañuelas sirve a media máquina; como segunda lectura de contexto y respaldo cuando Cañuelas cae varios días, sirve bien. No son dos fuentes del mismo dato: son dos capas.

## ROSGAN — descartada como automática, útil como índice

Dos problemas:

1. **Renderizado por JavaScript.** La página `/precios` trae el selector de remates vacío en el HTML crudo; los datos los inyecta el navegador. Scrapearla exigiría un navegador headless (Playwright), que es otra dependencia y otro costo operativo — desproporcionado para una fuente secundaria.
2. **Mide otra cosa.** Son resultados de remates por pantalla, con periodicidad de remate, no un precio de mercado diario por categoría.

Queda como **índice de referencia complementario** para el asesor financiero (Fase 5), cargado a mano o revisado de vez en cuando, no como conector automático.

## Diseño resultante para la Fase 4

Tres capas, de más a menos confiable:

1. **Cañuelas** — fuente **primaria diaria** por categoría (scraper, cp1252, rezago de un día).
2. **IPCVA** — segunda fuente automática, **mensual**, proveedor independiente. Conector server-rendered, corre semanal o mensual.
3. **Carga manual** — respaldo siempre disponible, y única vía para ROSGAN/otros.

Cada conector es una fila de `MarketSource` con su `slug` (`canuelas`, `ipcva`, `manual`, `rosgan`) y su propio módulo aislado, como ya prevé el documento 06. Que una fuente falle no debe frenar a las otras ni a ninguna métrica.

**Consecuencia de tener dos automáticas:** cuando difieran (van a diferir — miden cosas distintas y con distinto rezago), el sistema **no** debe promediarlas ni elegir una en silencio. Se guardan ambas con su `source`, y el dashboard o el asesor deciden cuál mostrar según el uso. Mezclarlas fabricaría un número que no publica nadie.

## Decisión que queda para cuando haya conector

**[DECISIÓN]** ¿La vista del IPCVA que se ingiere es "Precios en Pie" (`id=1`), que es la comparable con la hacienda de Cañuelas, o también "Precios al Gancho"? Propuesta: arrancar con Precios en Pie y sumar Gancho solo si el asesor financiero lo pide.
