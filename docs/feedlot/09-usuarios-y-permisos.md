# 09 · Usuarios y permisos (multiusuario, granular y escalable)

El sistema es multiusuario: distintas personas intervienen y cada una debe poder hacer **solo lo suyo**. Alguien solo carga datos, otro solo visualiza, otro carga pagos, otro hace mantenimiento. El módulo de permisos tiene que ser fino, específico por acción, y —como todo el proyecto— tiene que **escalar**: cada módulo nuevo trae sus permisos y los perfiles se recomponen sin reescribir código.

## Sobre qué se construye

El repositorio base ya define su regla de autorización (ADR-10): **Cognito autentica, Django autoriza**. La identidad viene de Cognito; los permisos viven en Django como Grupos + clases de permiso de DRF, nunca en Cognito. Este módulo extiende esa base, no la reemplaza.

## Los tres conceptos

```
Permiso atómico   →  una capacidad puntual: "cargar raciones", "ver cuenta corriente",
                     "registrar pagos", "ejecutar mantenimiento", "generar informes"...
Perfil (rol)      →  un conjunto de permisos con nombre: "Operador de carga",
                     "Cajero", "Encargado de mantenimiento", "Visualizador"...
Persona (usuario) →  se asigna a uno o más perfiles. Sus permisos efectivos son la
                     unión de los permisos de sus perfiles.
```

- **Los permisos son datos, no código.** Igual que el router del repo carga sus frases como filas (no como código nuevo), acá cada capacidad es una fila. Un módulo nuevo aporta sus permisos atómicos; no hay que programar autorización a mano cada vez. Un perfil nuevo es una fila más y sus asignaciones. **Esto es lo que hace escalar el módulo junto con el proyecto.**
- **Un perfil es un Grupo de Django** (respeta ADR-10). La granularidad fina se logra con permisos de dominio propios (definidos por módulo). Las clases de permiso de DRF los hacen cumplir en cada endpoint.

## Dos ejes de permiso

1. **Qué acciones** puede hacer (el perfil). Es lo primero a implementar.
2. **Sobre qué alcance** (qué clientes / qué establecimientos). Es permiso a nivel de objeto: un operador podría manejar solo ciertos clientes. Se suma cuando haga falta; el diseño lo contempla desde el vamos para no repintar después.

## Catálogo de permisos atómicos (inicial)

Nombrados `modulo:accion` (en inglés en el código; etiqueta en español en pantalla). Crecen con cada módulo.

| Módulo | Permisos atómicos |
|---|---|
| Clientes | `client:view`, `client:create`, `client:edit` |
| Hacienda | `animal:view`, `intake:create`, `weighing:create`, `death:create`, `exit:create` |
| Alimentación | `feed:view`, `feeding:create`, `feed_stock:manage`, `feed_delivery:create` |
| Sanidad | `health:view`, `health_event:create` |
| Servicios/costos | `service:view`, `service_charge:create`, `maintenance:execute` |
| Cuenta corriente | `ledger:view`, `payment:create`, `adjustment:create` |
| Dashboard | `dashboard:view` |
| Precios | `market:view`, `market:manage` |
| Asesores | `advisor:view`, `advisor:generate` |
| Administración | `user:manage`, `permission:manage`, `profile:manage` |

## Perfiles de ejemplo

| Perfil | Puede | No puede |
|---|---|---|
| **Operador de carga** | cargar raciones, pesajes, sanidad, ingresos | ver plata, registrar pagos, administrar usuarios |
| **Cajero / administrativo** | ver cuenta corriente, registrar pagos y ajustes | cargar hacienda o raciones |
| **Encargado de mantenimiento** | cargar servicios, ejecutar mantenimiento, uso de maquinaria/combustible | cuenta corriente, hacienda |
| **Visualizador** | ver dashboards e informes | cargar o modificar nada |
| **Contador** | ver cuenta corriente, precios e informes financieros | operar hacienda |
| **Administrador** | todo, incluido gestionar usuarios y permisos | — |

Los perfiles son **editables**: se ajustan tildando/destildando permisos, sin tocar código.

## Perfiles sugeridos por los asesores

Pediste que los perfiles los puedan armar los asesores para cada persona que interviene. El **asesor administrativo** ([05 · Asesores IA](feedlot/05-asesores-ia.md)) puede **proponer** la composición de un perfil según la función de la persona ("esta persona es peón de corral → debería tener `feeding:create`, `weighing:create`, `intake:create`, y nada de plata"). El flujo:

```
1. Se describe la función de la persona (o se elige de una lista).
2. El asesor administrativo propone un conjunto de permisos (un perfil sugerido).
3. Un administrador lo revisa y lo aplica (o lo ajusta).
```

Punto clave de seguridad: el asesor **propone, no otorga**. La asignación final siempre pasa por una persona con `permission:manage` (coherente con ADR-27 —los asesores son solo lectura y no ejecutan acciones— y con el "authorization lobby" que el repo ya trae). Así se gana la comodidad de que la IA arme el perfil sin ceder el control del acceso.

## Auditoría

Toda acción sensible (carga de pagos, ajustes, cambios de permisos) queda registrada con quién y cuándo. El repo ya tiene la base para esto (registro de solicitudes de acceso y del router); se extiende a los eventos operativos.

## Escalabilidad del módulo

- Un **rubro nuevo** (caballos, alfalfa, maquinaria) llega con sus propios permisos atómicos; los perfiles existentes se recomponen o se crean nuevos, sin reescribir la autorización.
- Un **permiso nuevo** es una fila; un **perfil nuevo** es una fila y sus asignaciones.
- El eje de **alcance por cliente/establecimiento** permite que crezca la organización (más gente, más clientes) sin que los permisos se vuelvan un enredo.

> Para el repo: esto amerita un ADR nuevo (p. ej. `adr-28-rbac-profiles`) que fije "permisos como datos, perfil = Grupo de Django, el asesor propone y el humano otorga", extendiendo ADR-10 sin contradecirlo. Se prepara junto al resto del paquete cuando avancemos a código.
