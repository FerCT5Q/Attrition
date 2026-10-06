# Draup data

<!-- BEGIN evaluate-attrition-variable:draup-data -->
## Conocimiento acumulado: Draup data

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:34:17-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** External pull factors
- **Relevancia:** El concepto no es evaluable hasta seleccionar un dataset, campo y uso específicos.

### Definición y fuente evaluadas

- **Definición vigente:** Señal de mercado laboral por definir proveniente de un feed licenciado de Draup.
- **Tipo semántico:** external_source
- **Tabla / fuente:** Fuente no validada o externa: No se encontró feed, propietario, grain, historia ni claves de join validados.
- **Columnas:** TBD
- **Grain:** Mercado laboral / geografía

### Relaciones con el portafolio

- Comparten survey_external (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Externa / tercero (2 puntos).
- **Scores:** Source=1, Definition=0, Coverage=0, Missingness=0, Consistency=1, History=0, Join=0, Effort=0
- **Coverage reciente:** None%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.
- No existe una racha estable que califique como historia utilizable. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos.
- La definición no puede considerarse confirmada hasta confirmar acceso aprobado, propietario, grain, historia, refresh y join de la fuente externa.
- No existe evidencia validada de coverage reciente.
- Missingness no puede cuantificarse sin observaciones validadas.

**Acciones recomendadas**

- Confirmar propietario, tablas, columnas, permisos y vigencia de la fuente; después repetir la auditoría de disponibilidad.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Lograr al menos 3 observaciones consecutivas con >= 95% de coverage.
- Aprobar la definición y confirmar acceso aprobado, propietario, grain, historia, refresh y join de la fuente externa; guardar SQL agregado, regla previa y métricas de reconciliación.
- Resolver brechas de elegibilidad u observabilidad y repetir el perfil; objetivo >= 95%.

**SQL y evidencia trazable**

- No existe SQL ejecutable para esta fuente.

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:draup-data -->
