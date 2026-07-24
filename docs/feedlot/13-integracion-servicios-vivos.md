# 13 · Runbook — integración con servicios vivos

> Los tres cabos que no se pueden cerrar sin el entorno real (sitios externos y AWS). Cada uno tiene su punto de integración marcado en el código. Este documento es el paso a paso para cerrarlos en Claude Code, con el inspector de red y credenciales AWS a mano.

## Cabo 1 — Formulario de fechas de Cañuelas

**Dónde:** `apps/market/connectors/canuelas.py`, método `fetch`.
**Qué falta:** hoy trae la vista por defecto (día actual, que suele venir provisorio). El reporte por rango de fechas se pide con el formulario "Fecha Inicial / Final", y no está confirmado si es GET o POST.

**Pasos:**

1. Abrí `https://www.mercadoagroganadero.com.ar/dll/hacienda1.dll/haciinfo000502` en el navegador con el inspector de red abierto (pestaña Network).
2. Completá una fecha pasada de día hábil (cerrado, no provisorio) y apretá BUSCAR.
3. En Network, mirá el request que se dispara: método (GET/POST), URL exacta, y los nombres de los campos de fecha (probablemente algo como `FechaIni` / `FechaFin` en formato DD/MM/AAAA).
4. Replicá ese request en `fetch`. Si es POST, usá `urllib.request` con `data=` codificada, o `httpx` (ya es dependencia del repo).
5. **Validá el parser contra HTML real:** guardá la respuesta de un día cerrado como `apps/market/tests/fixture_canuelas.html` (reemplazando el fixture sintético actual) y confirmá que `test_canuelas_parser.py` sigue verde. Si las categorías reales no matchean, ajustá el parser — la estructura de columnas ya está resuelta, lo que puede variar son los nombres de categoría.

**Criterio de hecho:** `python manage.py ingest_prices --source canuelas --date AAAA-MM-DD` trae filas reales y las persiste.

## Cabo 2 — Endpoint AJAX de IPCVA

**Dónde:** `apps/market/connectors/ipcva.py`, métodos `fetch` y `parse` (hoy lanzan `ConnectorError` a propósito).
**Qué falta:** "Precios en Pie" es un armador de gráficos; los números llegan por una llamada AJAX cuando se aplican los filtros. Hay que capturar esa llamada.

**Pasos:**

1. Abrí `https://ipcva.agrositio.com/estadisticas/vista_precios2.php?id=1` con el inspector de red.
2. Elegí categoría (p. ej. Novillos), país ARGENTINA, un rango de meses, y generá el gráfico.
3. En Network, buscá el request que devuelve los datos de la serie (XML o JSON). Anotá URL, parámetros y formato de respuesta.
4. Implementá `fetch` con esa URL/params y `parse` según el formato real. Devolvé una `ParsedPrice` por punto de la serie (mensual).
5. Escribí un fixture con una respuesta real y su test, igual que Cañuelas.

**Criterio de hecho:** `python manage.py ingest_prices --source ipcva` trae la serie mensual. Recordá: IPCVA es mensual y no se promedia con Cañuelas (adr-30 regla 8).

**Si el endpoint resulta inaccesible** (requiere token, CORS, etc.): IPCVA queda como carga manual y ROSGAN/otra fuente entra a evaluación. No forzar un scraping frágil; documentarlo y seguir con Cañuelas como única automática.

## Cabo 3 — Bedrock real para los asesores

**Dónde:** `apps/advisors/inference.py`, `AdvisorBedrockClient`.
**Qué falta:** el cliente sigue el patrón del router pero necesita configuración y verificación contra AWS.

**Pasos:**

1. Agregá `ADVISOR_BEDROCK_MODEL_ID` y confirmá `BEDROCK_REGION` en `config/settings.py`, y sumá ambas a `VARIABLES` (adr-15 regla 8).
2. Confirmá el permiso IAM `bedrock:InvokeModel` / `converse` sobre el modelo elegido.
3. Sumá un gate de conectividad tipo `bedrock_live` (como ya tiene el router en `test_bedrock_gate.py`) para que el deploy falle temprano si Bedrock no responde.
4. **Async (adr-16 regla 4):** el `generate` es síncrono a propósito. En el path async, envolvé con `asgiref.sync_to_async`, **nunca** `aiobotocore`. Confirmá que el endpoint POST no bloquee el event loop.
5. Corré la generación real contra un cliente de prueba y revisá que el `AdvisorReport` guarde `model_id`, `tokens` y `latency_ms` reales.

**Criterio de hecho:** un POST a `/api/advisor-reports/` en un entorno no-DEBUG genera texto real de Bedrock y persiste el reporte con su auditoría. Los tests siguen corriendo contra el mock (no se toca esa parte).

## Orden

Cañuelas primero (es la fuente primaria y desbloquea el dashboard de precios), después Bedrock (desbloquea los asesores de verdad), IPCVA al final (es redundancia, el sistema funciona sin él). Cada uno entra por su issue/PR.
