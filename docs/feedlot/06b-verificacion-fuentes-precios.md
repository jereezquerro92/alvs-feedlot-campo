# 06b · Verificación de fuentes de precios (julio 2026)

> Actualiza [06 · Precios de hacienda](06-precios-hacienda.md). Ese documento fue escrito sobre supuestos; esto es lo que se verificó consultando las fuentes.

**Fecha de verificación:** 2026-07-21.

## Resumen: la estrategia se invierte

El documento 06 daba a **datos.gob.ar como fuente primaria automatizable** y al scraping de Cañuelas como secundario. La verificación muestra lo contrario:

| Fuente | Estado verificado | Rol nuevo |
|---|---|---|
| datos.gob.ar (series) | **Sin datos vigentes de hacienda** | Descartada |
| Mercado Agroganadero (Cañuelas) | **Viva y publicando a diario** | **Primaria** |
| Carga manual | — | Respaldo (sin cambios) |

## Detalle

### datos.gob.ar — descartada

La API de series (`apis.datos.gob.ar/series/api/`) responde bien, pero no tiene precios de hacienda vigentes:

- Búsqueda `novillo` → **una sola serie**, `AGRO_0227` ("Peso de novillo por kilo vivo"), con `time_index_end` en **2019-08-01**. Discontinuada hace siete años.
- Búsqueda `hacienda` → **cero resultados**.
- Búsqueda `bovino precio` → 78 resultados, ninguno de precio de hacienda (leche cruda hasta 2008, IPC provinciales, índices de comercio exterior).

El endpoint CKAN clásico (`datos.gob.ar/api/3/action/…`) devolvió respuesta vacía en todos los intentos.

**Conclusión:** no hay serie oficial abierta y actualizada de precio de hacienda. El Índice Novillo SIO Carnes que menciona el documento 06 no está expuesto por esta vía.

### Mercado Agroganadero (Cañuelas) — primaria

El sitio está activo y sirvió una tabla de precios por categoría fechada el mismo día de la consulta. Publica varias vistas, todas accesibles sin login:

| Vista | Ruta |
|---|---|
| Precios por Categoría (Resol. 2018-32) | `/dll/hacienda1.dll/haciinfo000502` |
| Analítico de Precios (Clasificación MAG) | `/dll/hacienda6.dll/haciinfo000224` |
| Resumen de Precios (Clasificación MAG) | `/dll/hacienda6.dll/haciinfo000225` |
| Precios por Categoría (Clasificación Ruca) | `/dll/hacienda1.dll/haciinfo000002` |
| Precio Novillitos 401/420 | `/dll/hacienda6.dll/haciinfo000307` |
| Índice General MAG por período | `/dll/hacienda2.dll/haciinfo000014` |

La tabla de precios por categoría trae, por categoría: mínimo, máximo, promedio, mediana, cabezas, importe, kilos y promedio de kilos. Es más rico que lo que el modelo `MarketPrice` contempla hoy.

## Detalles técnicos para el conector

Tres cosas detectadas que van a morder si no se contemplan:

1. **Encoding.** El sitio sirve **Windows-1252**, no UTF-8. "Mínimo" llega como `M�nimo` si se decodifica mal. El conector debe decodificar explícitamente como `cp1252`.

2. **Rango de fechas por formulario.** Las vistas tienen campos "Fecha Inicial" y "Final" que se envían al DLL. Hay que determinar si acepta GET con parámetros o exige POST — se resuelve inspeccionando el formulario al implementar.

3. **Precios provisorios.** La consulta del mismo día devolvió el encabezado "PRECIOS PROVISORIOS" con la tabla vacía: los datos del día se cargan más tarde. El conector debe correr con **rezago de al menos un día** y estar preparado para recibir tabla vacía sin romper.

## Consecuencias para el diseño de la Fase 4

- **El scraper deja de ser el plan B y pasa a ser el único camino automático.** Eso sube su criticidad: necesita monitoreo real (alerta cuando la ingesta devuelve vacío N días seguidos, o valores fuera de rango), no un `try/except` silencioso.
- **La carga manual gana peso.** Si el scraper es el único automático y el sitio cambia el HTML, la carga manual es lo único que queda. Tiene que ser cómoda de usar, no un formulario de emergencia.
- **`MarketPrice` conviene ampliarlo.** Hoy tiene `price_per_kg`; la fuente da mínimo, máximo, promedio, mediana y volumen. Guardar solo el promedio tira información que el asesor financiero podría usar. El campo `raw` mitiga, pero conviene modelar min/max/mediana y cabezas como columnas.
- **[DECISIÓN]** ¿Se evalúan ROSGAN o IPCVA como segunda fuente automática? No se verificaron en esta pasada. Tener una sola fuente automática es un punto único de falla.
