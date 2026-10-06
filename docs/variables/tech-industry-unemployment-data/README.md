# Tech industry unemployment data

<!-- BEGIN evaluate-attrition-variable:tech-industry-unemployment-data -->
## Conocimiento acumulado: Tech industry unemployment data

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:34:11-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** External pull factors
- **Relevancia:** La estrechez del mercado laboral puede contextualizar el riesgo de attrition voluntario.

### Definición y fuente evaluadas

- **Definición vigente:** Tasa periódica de desempleo de la industria tecnológica mapeada a una geografía laboral aprobada.
- **Tipo semántico:** external_source
- **Tabla / fuente:** Fuente no validada o externa: No se ha aprobado proveedor, definición de industria ni mapping geográfico; también importan lag de publicación y vintages.
- **Columnas:** external date, external geography, unemployment_rate, labor_market, country, region, fis_mo_end_dt
- **Grain:** Geografía-periodo

### Relaciones con el portafolio

- Comparten country (shared_source_column).
- Comparten fis_mo_end_dt (shared_source_column).
- Comparten region (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten group_category_level (shared_semantic_cue).
- Comparten ratio_rate_percent (shared_semantic_cue).
- Comparten survey_external (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Externa / tercero (4 puntos).
- **Scores:** Source=1, Definition=0, Coverage=0, Missingness=0, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** None%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- No existe una ruta confiable y validada para construir la definición solicitada. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.
- La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos.
- No existe una ruta confiable y validada para construir la definición solicitada.
- No existe evidencia validada de coverage reciente.
- Missingness no puede cuantificarse sin observaciones validadas.

**Acciones recomendadas**

- Identificar una fuente aprobada o excluir la variable del conjunto candidato.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Confirmar propietario, tablas, columnas, permisos y vigencia de la fuente; después repetir la auditoría de disponibilidad.
- Resolver brechas de elegibilidad u observabilidad y repetir el perfil; objetivo >= 95%.
- Investigar brechas por fecha y segmento elegible; objetivo <= 5% sin patrón sistemático.

**SQL y evidencia trazable**

- No existe SQL ejecutable para esta fuente.

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:tech-industry-unemployment-data -->
