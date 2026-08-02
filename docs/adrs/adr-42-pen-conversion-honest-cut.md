---
title: adr-42-pen-conversion-honest-cut
type: adr
category: backend
use_case: leer o cambiar la conversión por corral, atribuir engorde a un corral, componer el cierre por corral
created: 2026-07-25
modified: 2026-08-02
tags: [adr, feedlot, feedyard, metrics, conversion, pen, phase-4b]
---

# ADR-42 — Conversión por corral: el corte honesto

## CONTEXT

> La mitad de ganancia del cierre por corral, que estaba diferida porque un kilo de engorde no sabe en qué corral se puso. Con `PenPlacement` se atribuye el subconjunto honesto —los tramos que el animal pasó enteros en un corral— y lo ambiguo se declara no calculable.

## ASSERTIONS

1. `pen_conversion(*, pen, start, end)` es una función pura en `apps.metrics`, hermana de `pen_occupancy_report` y `pen_cost_summary`. No hay tabla ni migración: la conversión es una afirmación derivada, no un dato almacenado ([[adr-29-metrics-derivation]] regla 1).
2. Un tramo de pesaje se atribuye al corral donde el target estaba al pesaje anterior, y sólo si no hubo ningún `PenPlacement` estrictamente dentro del intervalo y ese corral es el que se está midiendo. La ubicación se deriva de los eventos `in`/`out` ([[adr-34-pen-placement]] regla 1): un `in` fija el corral, un `out` lo libera.
3. Lo no atribuible se cuenta. Un tramo cuyo ADG ya es no calculable ([[adr-28-animal-lifecycle-and-sanitary]] regla 2) se saltea (`segments_skipped`); uno calculable que no se puede fijar a una sola estadía —cambió de corral, o el target no tiene placement acá— cuenta como `segments_unattributed`. Los kilos se suman sólo sobre `segments_attributed`.
4. `pen_conversion` devuelve `null` con su `not_calculable` cuando no hay tramo atribuible (`no_attributable_growth`), cuando el engorde atribuido salió plano o negativo (`no_weight_gain`) o cuando no hay alimento registrado al corral en el período (`no_feed_recorded`). Nunca un cero de relleno.
5. Es lectura pura: no postea asiento, no muta nada y no agrega variables ni endpoints en este cut. Se entrega como función de servicio testeada, con la misma exposición que sus hermanas, hasta que exista un dashboard de corrales que las consuma.
6. `pen_closeout(*, pen, start, end)` compone la mitad de ocupación con la de conversión en un solo cierre por corral, y cada mitad carga su propio `not_calculable`. La conversión por cliente no cambia: esta métrica es su desagregado por corral.

## FORBIDDEN

- **NEVER** atribuir a un corral un tramo en el que el animal cambió de corral (regla 2). El engorde se repartió de una forma que los datos no registran, y asignarlo entero a uno es el número inventado que [[adr-29-metrics-derivation]] regla 2 prohíbe.
- **NEVER** devolver cero cuando no hay nada atribuible (regla 4). Un cero se grafica igual que un cero real y puede justificar una decisión de compra.
- **NEVER** omitir los contadores de tramos (regla 3). Sin ellos no se distingue "el corral no engordó" de "no pudimos atribuirle el engorde".
- **NEVER** almacenar la conversión como dato (regla 1). Queda vieja con el próximo pesaje y crea una segunda definición del número.

## REJECTED

- **Prorratear el engorde entre corrales** — repartir el tramo partido según los días en cada corral. Rechazado: la proporción no está en los datos, así que el reparto sería una estimación presentada como medición.
- **Atribuir el tramo al corral del pesaje final** — una regla simple para no perder tramos. Perdió contra la regla 2: le regala a un corral el engorde que otro produjo.
- **Exponer un endpoint sólo para esta métrica** — publicarla antes que a sus dos hermanas. Rechazado por asimetría y por agregar una ruta sin consumidor; las tres se exponen juntas cuando exista el dashboard que las use.

## RELATED

### related adrs

- [[docs/adrs/adr-34-pen-placement]] — regla 1, los eventos que hacen posible la atribución
- [[docs/adrs/adr-33-feedyard-operating-loop]] — la mitad de costo del cierre por corral
- [[docs/adrs/adr-29-metrics-derivation]] — reglas 1 a 3, derivar, no inventar, y contar lo salteado
- [[docs/adrs/adr-28-animal-lifecycle-and-sanitary]] — regla 2, el ADG no calculable

### related files

- [[docs/FEEDLOT]] — el cierre por corral en la operación
- [[docs/FEEDLOT-DATA-MODEL]] — `PenPlacement`, `Weighing`, `FeedingEvent`
