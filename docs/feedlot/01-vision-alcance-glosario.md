# 01 · Visión, alcance y glosario

## Visión

Un sistema de trazabilidad para un feedlot que opera con **hacienda propia** y con **hotelería** (engorde a corral de animales de terceros a los que se les factura alimentación y servicios). El objetivo es que cada peso gastado en un animal quede registrado, atribuido a su dueño y cruzado contra su resultado (crecimiento, conversión, mortandad, venta), y que esa información alimente decisiones —del productor, del contador y del administrador— y se pueda ampliar mañana a otros rubros del campo.

Tres pilares:

- **Registrar sin fricción.** La carga diaria (comida, pesajes, sanidad, ingresos y egresos) tiene que ser rápida y tolerar las dos formas reales de trabajar: animal por animal con caravana, o por lote con kilos totales.
- **Costear con verdad.** Todo insumo del feedlot que se aplica a un animal impacta la cuenta corriente del cliente en pesos, al valor del día. La cuenta es un libro contable, no una planilla editable.
- **Devolver inteligencia.** Dashboards, precios de referencia y asesores que transforman los registros en métricas y recomendaciones.

## Alcance por fases (resumen)

El detalle del plan está en [07 · Arquitectura escalable y roadmap](07-arquitectura-escalable-y-roadmap.md). En una línea:

- **Fase 1 — Núcleo operativo:** clientes y cuenta corriente, ingreso de animales (individual y lote), catálogo y stock de alimento, carga de raciones con costeo, pagos.
- **Fase 2 — Ciclo del animal:** pesajes y crecimiento, muertes, salidas, sanidad.
- **Fase 3 — Dashboard y métricas** por cliente.
- **Fase 4 — Precios de hacienda** (ingesta automática + manual).
- **Fase 5 — Asesores IA.**
- **Fase 6+ — Multi-rubro** (caballos, alfalfa, taller, maquinaria).

### Dentro y fuera de alcance (Fase 1–2)

Dentro: gestión de clientes, animales y lotes, alimentación con doble origen (propio / del cliente), stock de alimento, sanidad, cuenta corriente en ARS con precio histórico, pagos, y la trazabilidad de todos esos eventos.

Fuera (por ahora, se suma después): facturación fiscal/AFIP, integración con balanzas/hardware de pesaje, remitos y guías de traslado (DTe/DTA), nómina, y los rubros no ganaderos.

## Principios de diseño

Heredados del repositorio base y adoptados como propios:

- **Se crece por adición.** Una capacidad nueva es una app de dominio nueva; la base no se toca. Esto es lo que hace escalable el multi-rubro.
- **Eventos inmutables.** Cada hecho operativo (una ración, un pesaje, una muerte, un pago) es un registro que no se edita ni se borra. Los saldos y las métricas se **derivan** de esos eventos. Las correcciones se hacen con eventos de ajuste.
- **Precio del momento.** Cada movimiento con costo guarda el precio unitario y la cantidad tal como estaban ese día. Aunque el precio del alimento suba mañana, lo cargado ayer no cambia.
- **Código en inglés, pantalla en español.** Por convención del repo, todos los identificadores (modelos, campos, endpoints) van en inglés; el idioma del usuario vive solo en lo que se renderiza en el frontend. Por eso el glosario de abajo fija el nombre canónico en inglés de cada término.

## Glosario del dominio

Nombre canónico (inglés) que usará el código, con su significado de negocio. Es la autoridad de nombres del dominio feedlot; se integra al `GLOSSARY` del repo.

| Término (negocio) | Canónico (código) | Significado |
|---|---|---|
| Cliente | `Client` | Dueño de la hacienda. Puede ser de tipo `boarding` (hotelería, tercero) o `own` (el propio feedlot, para costear su hacienda propia). |
| Cuenta corriente | `Account` | La cuenta de un cliente. Su saldo se deriva del libro de movimientos, no se guarda como número editable. |
| Animal | `Animal` | Cabeza individual identificada por caravana. Tiene categoría, sexo, estado y peso actual (derivado del último pesaje). |
| Caravana | `ear_tag` | Código de la etiqueta de oreja; identifica al animal. |
| Lote | `Lot` | Conjunto de animales manejado por cabezas + kilos totales, sin individualizar. Puede ser anónimo (solo cabezas y kg) o agrupar animales individuales. |
| Categoría | `category` | Vaca, toro, novillo, novillito, vaquillona, ternero/a (`cow`, `bull`, `steer`, `heifer`, `calf`, …). |
| Ingreso | `Intake` | Evento de alta de hacienda para un cliente, en modo individual (crea `Animal`) o lote (crea/actualiza un `Lot`). |
| Pesaje | `Weighing` | Registro de peso de un animal o de un lote (kg totales) en una fecha. El crecimiento se deriva de pesajes sucesivos. |
| Muerte / baja | `Death` | Evento que marca un animal como muerto o reduce cabezas y kilos de un lote. |
| Salida / egreso | `Exit` | Evento de venta o retiro de un animal, o parte de un lote (cabezas + kg). |
| Tipo de alimento | `FeedType` | Ítem del catálogo de alimentos (maíz, silaje, balanceado, etc.), con su unidad. |
| Entrega de alimento | `FeedDelivery` | Alimento que **aporta el cliente** y entra a su stock. |
| Movimiento de stock | `FeedStockMovement` | Entrada o salida de stock de alimento; el saldo de stock se deriva sumándolos. Hay stock propio del feedlot y stock por cliente. |
| Ración / alimentación | `FeedingEvent` | Registro diario de alimento dado a un lote/animal: tipo, kg, precio del momento y **origen** (stock del cliente o stock propio). |
| Producto sanitario | `HealthProduct` | Ítem del catálogo de vacunas/tratamientos, con su precio. |
| Sanidad | `HealthEvent` | Aplicación de una vacuna o tratamiento a un animal/lote, con dosis y costo. |
| Movimiento de cuenta | `LedgerEntry` | Asiento inmutable en la cuenta de un cliente: débito (cargo) o crédito (pago/ajuste), en ARS, con referencia al evento que lo originó. |
| Pago | `Payment` | Dinero que ingresa el cliente; genera un `LedgerEntry` de crédito. |
| Precio de hacienda | `MarketPrice` | Precio de referencia ($/kg) de una categoría en una fuente y fecha (Cañuelas, Liniers/SIO, ROSGAN…). |
| Fuente de precios | `MarketSource` | Origen de un precio de hacienda (mercado o índice). |
| Asesor | `Advisor` | Uno de los tres perfiles de análisis con IA. |
| Informe de asesor | `AdvisorReport` | Análisis generado por un asesor sobre los datos de un cliente en un período. |

> **Nota de convención:** las categorías, estados y conceptos se implementan como *choices* de Django con etiqueta traducida al español en el frontend; la clave interna queda en inglés (`cow`, `dead`, `feed`, …).
