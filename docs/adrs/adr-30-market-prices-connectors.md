---
title: adr-30-market-prices-connectors
type: adr
category: backend
use_case: escribir o arreglar un conector de precios, ingerir una fecha, elegir una fuente de referencia, testear un parser contra un fixture
created: 2026-07-23
modified: 2026-08-02
tags: [adr, feedlot, market, prices, connectors]
---

# ADR-30 — Precios de referencia y conectores de fuentes

## CONTEXT

> Los precios de hacienda son un valor de mercado externo, de referencia: no son la moneda de la cuenta, que sigue en ARS con precio histórico. Cada fuente entra por un conector que separa la red del parseo y falla de forma distinguible.

## ASSERTIONS

1. Cañuelas es la fuente primaria diaria y datos.gob.ar está descartada: su serie oficial de novillo terminó en 2019, verificado contra el sitio vivo.
2. IPCVA es la segunda fuente automática —páginas renderizadas en servidor, redundancia mensual de un proveedor independiente— y ROSGAN queda de carga manual, porque arma su tabla con JavaScript y publica remates periódicos, no un precio diario.
3. Cada conector separa `fetch` (trae bytes, usa red) de `parse` (interpreta, puro). Los tests apuntan a `parse` contra un fixture fijo, nunca al sitio real.
4. El parser mapea columnas leyendo la fila de encabezado, nunca por posición. Si el sitio reordena columnas los valores no se deslizan al campo equivocado, y si el encabezado desaparece falla en vez de guardar basura.
5. Tres estados se distinguen: página provisoria del día en curso → vacío, no es error; tabla presente sin filas (día sin operaciones) → vacío; tabla ausente (el HTML cambió) → `ConnectorError`.
6. La ingesta es idempotente por `(fuente, categoría, fecha)`: reingerir actualiza la fila, no la duplica. El payload crudo se guarda en `raw` para rehacer el parseo sin volver a pedir.
7. Una fuente caída no frena a las demás: `ingest_prices` aísla cada una, registra la falla y sigue. Ante un hueco, `latest_price` devuelve el último valor conocido.
8. Dos fuentes automáticas nunca se promedian. Cañuelas es diaria de mercado físico en ARS e IPCVA es un índice mensual en USD/kg: miden cosas distintas con distinto rezago, se guardan separadas por su `source` y elige el consumidor.
9. `MarketPrice` guarda mínimo, máximo, promedio, mediana y cabezas, no sólo el promedio, porque las fuentes los publican y el asesor puede usarlos.

## FORBIDDEN

- **NEVER** promediar dos fuentes (regla 8). Fabricaría un número que no publica ninguna, y con unidades distintas ni siquiera es un promedio.
- **NEVER** mapear columnas por posición (regla 4). Un reordenamiento del sitio guarda precios en el campo equivocado sin fallar.
- **NEVER** confundir "no hubo operaciones" con "el HTML cambió" (regla 5). El segundo caso pasaría inadvertido durante días leyéndose como un mercado quieto.
- **NEVER** testear un parser contra el sitio vivo (regla 3). El sitio se cae y cambia, y el test dejaría de decir si el parser está bien.
- **NEVER** tapar la falla de un conector con un `try/except` silencioso (regla 7). El aislamiento por fuente existe para registrar la falla, no para esconderla.

## REJECTED

- **datos.gob.ar como fuente primaria** — la estrategia que asumía el documento 06. Cayó al verificarla: la serie oficial de novillo termina en 2019. Reabriría sólo si el organismo la retomara.
- **ROSGAN como fuente automática** — descartada por construcción del sitio: la tabla la arma JavaScript y lo que publica son remates periódicos, no un precio diario. Queda como índice de carga manual.
- **Promediar Cañuelas e IPCVA en un precio único** — un solo número de referencia, más cómodo para el dashboard. Rechazado por la regla 8; la comodidad del consumidor no justifica inventar la serie.

## RELATED

### related adrs

- [[docs/adrs/adr-25-account-ledger]] — regla 3, por qué la cuenta no se redenomina con estos precios
- [[docs/adrs/adr-39-gross-margin-and-fx]] — el margen que consume este precio de referencia
- [[docs/adrs/adr-29-metrics-derivation]] — el contrato del hueco que `latest_price` respeta

### related files

- [[docs/feedlot/06-precios-hacienda]] — las fuentes, sus URLs y sus formularios
- [[docs/feedlot/06b-verificacion-fuentes-precios]] — la verificación contra los sitios vivos
- [[docs/feedlot/06c-segunda-fuente-automatica]] — IPCVA, su serie y su salvedad de unidad
- [[docs/FEEDLOT-DATA-MODEL]] — `MarketPrice` y `MarketSource`
