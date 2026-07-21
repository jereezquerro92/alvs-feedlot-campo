# 05 · Asesores con IA

Tres asesores que leen los datos de un cliente y devuelven una mirada experta. No reemplazan al productor, al contador ni al administrador: les ahorran el trabajo de mirar todos los números y les señalan dónde mirar.

## Los tres perfiles

| Asesor | `slug` | Mirada | Ejemplos de lo que aporta |
|---|---|---|---|
| **Ganadero y agrícola** | `livestock` | Producción a corral y del campo | Evalúa GDP y conversión contra referencias; detecta lotes que engordan poco para lo que comen; observa mortandad y su timing; sugiere ajustes de dieta o manejo; mira el rubro con ojo agronómico. |
| **Contable y financiero** | `finance` | Plata, crecimiento y punto de venta | Analiza la evolución del saldo y el costo por kilo puesto; cruza el costo acumulado contra el precio de hacienda de referencia para estimar el **punto de venta** conveniente; señala clientes con saldo creciente o cobranza demorada. |
| **Administrativo** | `admin` | Control y prolijidad | Detecta huecos de carga (días sin ración, pesajes atrasados, stock en negativo), inconsistencias, y puntos a mejorar en el control operativo. |

## Cómo funcionan

Cada asesor es un análisis **generativo** sobre los datos **propios del cliente**. El flujo:

```
1. Se arma un "contexto" con las métricas del cliente en un período
   (consumo, costeo, GDP, conversión, mortandad, saldo, precios de referencia).
2. Ese contexto + el prompt del rol del asesor se envían al modelo (AWS Bedrock).
3. El modelo devuelve recomendaciones en texto estructurado.
4. Se guarda como AdvisorReport (con el snapshot de entrada, para poder reproducirlo).
```

Puntos de diseño:

- **Fundado en datos, no inventado.** El asesor solo razona sobre las métricas que se le pasan; no consulta la base por su cuenta ni ejecuta acciones. Es **solo lectura**.
- **Acotado por cliente.** Un informe es siempre de un cliente y un período. Nunca mezcla datos de distintos clientes.
- **Auditable y reproducible.** Se guarda qué datos entraron, qué modelo se usó, cuántos tokens y cuánto tardó. Se puede volver a leer el informe tal cual se generó.
- **Con control de costo.** Los informes se generan a pedido (o programados), no en cada carga. Se puede limitar frecuencia y tamaño de contexto.

## Relación con el "router" del repo

El repositorio base ya trae una capa de chat que es un **router de enum cerrado**: elige entre opciones predefinidas y **no genera texto libre** (por diseño, ADR-15). Los asesores son lo contrario: **sí generan** análisis. Por eso no se cuelgan del router; son una **capacidad nueva** con su propio endpoint y sus propias barreras. Esa distinción —y la excepción explícita al principio de "cero generación"— queda formalizada en el **ADR-27 — Advisors (generative capability)**, para no romper la coherencia del harness.

## Entregable

Un informe de asesor puede mostrarse en el dashboard del cliente (panel "Recomendaciones") y/o exportarse. **[DECISIÓN]:** definir si los informes se generan a demanda (botón "Analizar"), de forma programada (semanal por cliente), o ambas. Por defecto: a demanda en Fase 5, con opción programada después.
