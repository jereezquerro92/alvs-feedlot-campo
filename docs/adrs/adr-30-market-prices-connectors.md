# ADR-30 — Precios de referencia y conectores de fuentes

**Estado:** propuesto (Fase 4)
**Contexto:** implementa [[06-precios-hacienda]] con las correcciones de [[06b-verificacion-fuentes-precios]] y [[06c-segunda-fuente-automatica]].

## Contexto

El sistema necesita precios de hacienda de referencia para métricas y para el
asesor financiero. No son la moneda de la cuenta —esa sigue en ARS con precio
histórico— sino un valor de mercado externo. El documento 06 asumió fuentes que,
verificadas, resultaron distintas de lo esperado.

## Decisiones

### 1. Cañuelas es la fuente primaria, no datos.gob.ar

La serie oficial de novillo de datos.gob.ar terminó en 2019 (verificado). El
Mercado Agroganadero de Cañuelas publica precios diarios por categoría y está
vivo. Se invierte la estrategia del documento 06: Cañuelas primaria, datos.gob.ar
descartada.

### 2. IPCVA es la segunda fuente automática; ROSGAN queda manual

IPCVA sirve páginas renderizadas en servidor (scrapeables); ROSGAN arma su tabla
con JavaScript y publica remates periódicos, no un precio diario. IPCVA da
redundancia mensual de un proveedor independiente; ROSGAN queda como índice de
carga manual. Detalle en [[06c-segunda-fuente-automatica]].

### 3. `fetch` y `parse` son pasos separados

Cada conector separa el traer bytes (`fetch`, con red) del interpretarlos
(`parse`, puro). Así el parser se testea contra un fixture fijo sin depender del
sitio real, que se cae y cambia. Los tests apuntan a `parse`.

### 4. El parser lee el encabezado para mapear columnas

El conector de Cañuelas no asume el orden de las columnas: lee la fila de
encabezado y mapea nombre→índice. Si el sitio reordena columnas, los valores no
se deslizan en silencio al campo equivocado; y si el encabezado desaparece, falla
con error en vez de guardar basura.

### 5. Tres estados distintos, tres respuestas distintas

- **Página provisoria** (mismo día, datos sin cerrar) → devuelve vacío, no es error.
- **Tabla presente sin filas** (día sin operaciones) → devuelve vacío.
- **Tabla ausente** (el HTML cambió) → `ConnectorError`.

Confundirlos haría que un cambio de la web se lea como "no hubo precios" y pase
inadvertido durante días.

### 6. Ingesta idempotente por (fuente, categoría, fecha)

Reingerir una fecha actualiza la fila, no la duplica. Misma disciplina que el
resto del sistema: la fuente es la verdad, la fila es cache de la última lectura.
El payload crudo se guarda en `raw` para rehacer el parseo sin volver a pedir.

### 7. Falla de una fuente no frena a las demás

El comando `ingest_prices` aísla cada fuente: si una se cae o cambió su HTML, lo
registra y sigue con las otras. Ninguna métrica depende de que una fuente externa
esté siempre arriba; ante un hueco, `latest_price` devuelve el último valor conocido.

### 8. Dos fuentes automáticas no se promedian

Cañuelas (diaria, mercado físico) e IPCVA (mensual, índice) miden cosas distintas
con distinto rezago. Van a diferir. El sistema guarda ambas con su `source` y deja
que el dashboard o el asesor elijan según el uso. Promediarlas fabricaría un número
que no publica ninguna fuente.

## Puntos de integración pendientes (para Claude Code, contra el sitio vivo)

Dos cosas no se pueden cerrar sin el sitio real y quedan marcadas en el código:

1. **Cañuelas — formulario de fechas.** El `fetch` actual trae la vista por
   defecto; el rango por fecha puede exigir POST. Confirmar los parámetros con el
   inspector de red y completar `fetch`. El fixture de test debe reemplazarse por
   una página real de un día cerrado.
2. **IPCVA — endpoint de datos.** "Precios en Pie" es un armador de gráficos; los
   números llegan por una llamada AJAX. Capturar esa llamada, y completar `fetch` y
   `parse` de `IpcvaConnector` (hoy lanzan `ConnectorError` a propósito, para no
   inventar un formato no verificado).

## Consecuencias

- El scraper de Cañuelas es el único camino automático diario: necesita monitoreo
  real (alerta ante N días vacíos o valores fuera de rango), no un `try/except`
  silencioso. El aislamiento por fuente lo habilita; la alerta se suma al operarlo.
- El modelo `MarketPrice` guarda min/max/promedio/mediana/cabezas, no solo el
  promedio, porque las fuentes los dan y el asesor podría usarlos.
