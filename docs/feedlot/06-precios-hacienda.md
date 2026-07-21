# 06 · Precios de hacienda (valores de referencia)

El sistema necesita traer precios de referencia de hacienda de mercados argentinos, para valorizar métricas y alimentar al asesor financiero (estimar el punto de venta). La cuenta corriente sigue siendo en ARS con precio histórico; estos precios son **referencia**, no la moneda de la cuenta.

## Fuentes evaluadas

| Fuente | Qué da | Acceso programático | Recomendación |
|---|---|---|---|
| **datos.gob.ar / datos.agroindustria.gob.ar** — *Índice Novillo SIO Carnes (INSC)* y *Mercado de Liniers (precios, cantidad, peso promedio)* | Precio promedio ponderado, por categoría y zona | **Sí** — portal CKAN (API + CSV), licencia CC-BY 4.0, actualización periódica | **Fuente primaria automatizable.** Es dato oficial y abierto. |
| **Mercado Agroganadero de Cañuelas (MAG)** — mercadoagroganadero.com.ar | Precios diarios por categoría (Clasificación Ruca), índice general | No hay API oficial; datos en páginas web | **Fuente secundaria vía scraping** para el precio diario por categoría. |
| **ROSGAN** — rosgan.com.ar/indices | Índices y resultados de remates | No hay API; informes web/PDF | Referencia complementaria; ingesta manual o scraping puntual. |
| **IPCVA** — ipcva.com.ar | Informes y series de precios | Informes/PDF | Referencia de contexto; manual. |
| **Carga manual / override** | Lo que cargue el operador | — | **Siempre disponible** como respaldo y para corregir. |

## Estrategia de ingesta

Un modelo simple y a prueba de fallas de fuente:

- Un **catálogo de fuentes** (`MarketSource`) y una tabla de **precios** (`MarketPrice`: fuente, categoría, fecha, $/kg, más el payload original para auditoría).
- **Conectores por fuente**, cada uno aislado:
  - `sio-carnes` / `liniers` → cliente de la **API CKAN** de datos.gob.ar (descarga el CSV/recurso y lo normaliza). Automatizable con una tarea programada.
  - `canuelas` → scraper del sitio del MAG para el precio diario por categoría.
  - `manual` → carga por el operador desde el admin.
- **Tarea programada** (diaria o según publique cada fuente) que corre los conectores automáticos y agrega filas nuevas sin pisar las viejas (mismos criterios de inmutabilidad del resto del sistema).
- **Tolerancia a fallas:** si una fuente no responde, el sistema sigue con la última conocida y con la carga manual. Ninguna métrica depende de que una fuente externa esté siempre arriba.

## Uso en el sistema

- **Métricas/dashboard:** graficar el precio de referencia junto al costo acumulado por kilo puesto, para leer margen.
- **Asesor financiero:** estimar el punto de venta cruzando costo vs. precio de mercado.
- **[DECISIÓN] — Equivalente en kilos de novillo.** Hoy la cuenta es en ARS. Si más adelante querés una lectura anti-inflación, con estos mismos precios se puede mostrar (solo como métrica informativa) el equivalente de cada movimiento en kg de novillo del día. No cambia la cuenta; se agrega como columna calculada.

> Nota técnica: el fetch de estas fuentes lo hace el **backend** con sus propias reglas de red; los conectores viven en la app `market`. Se documentan las URLs de recurso exactas al implementar cada conector (Fase 4), porque el portal CKAN versiona los recursos.
