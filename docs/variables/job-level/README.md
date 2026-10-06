# Job level

## Campos

| Campo | Explicación simple | Cardinalidad observada |
|---|---|---:|
| `job_level_primary_position` | Nivel detallado de la posición principal. | 45 |
| `level_grouped` | Versión resumida de los niveles detallados. | 9 |
| `management_level` | Banda de jerarquía organizacional. | 6 |

Los tres campos tuvieron 100% de cobertura en la población activa revisada y 72 meses de historia utilizable en el último profile.

## Cómo se relacionan

`job_level_primary_position` y `level_grouped` describen el nivel del puesto con distinta granularidad. Normalmente varios valores detallados terminan en el mismo grupo.

`management_level` responde a otra pregunta: ubica a la persona en una banda jerárquica comparable, pero no demuestra por sí solo que tenga personas a cargo. Un technical leader puede estar en una banda alta sin ser manager directo.

Dos personas con el mismo `management_level` están en una banda similar; eso no significa que una reporte a la otra ni que tengan la misma responsabilidad. La relación de reporte se valida con `manager_employee_id`.

## Uso en attrition

- `level_grouped`: preferido para cohortes y reporting por su estabilidad y bajo número de categorías.
- `job_level_primary_position`: útil para el modelo y para análisis más precisos con cohort minimum.
- `management_level`: útil para controlar seniority y comparar patrones por banda jerárquica.
- Para distinguir people managers de individual contributors se necesita además un indicador de manager o conteo de reportes.

## Ejemplo

Si dos ingenieros tienen el mismo `management_level`, se puede decir que pertenecen a una banda jerárquica comparable. No se puede concluir que ambos sean directores, que manejen procesos idénticos o que uno esté arriba del otro sin revisar su posición y cadena de reporte.

<!-- BEGIN evaluate-attrition-variable:position-time-in-level -->
## Conocimiento acumulado: Position / time in level

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:34:50-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Tenure
- **Relevancia:** El tiempo en nivel puede identificar progresión estancada o avance reciente.

### Definición y fuente evaluadas

- **Definición vigente:** Tiempo desde la fecha efectiva de entrada al nivel, con contexto opcional de tenure en rol.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** levelentrydate, time_in_role, time_in_job_profile_start_date
- **Grain:** Snapshot de empleado

### Relaciones con el portafolio

- Comparten levelentrydate (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten flag_event (shared_semantic_cue).
- Comparten group_category_level (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Pendiente.
- La prueba aporta contexto para interpretar el concepto, pero no es un requisito definitorio y no puede elevar el score.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_25_position-time-in-level_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_25_position-time-in-level_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_25_position-time-in-level_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_25_position-time-in-level_time-in-role_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:position-time-in-level -->

<!-- BEGIN evaluate-attrition-variable:promoted-vs-hired-into-level -->
## Conocimiento acumulado: Promoted vs. hired into level

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:36:12-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Career progression
- **Relevancia:** La vía de entrada al nivel distingue progresión interna de colocación externa.

### Definición y fuente evaluadas

- **Definición vigente:** Clasifica la entrada al nivel actual como promoción, contratación o desconocida usando sólo eventos conocidos al snapshot.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** levelentrydate, is_promo, promotion_date, original_hire_date, max_hire_rehire_date
- **Grain:** Snapshot de empleado / evento

### Relaciones con el portafolio

- Comparten is_promo (shared_source_column).
- Comparten levelentrydate (shared_source_column).
- Comparten max_hire_rehire_date (shared_source_column).
- Comparten original_hire_date (shared_source_column).
- Comparten promotion_date (shared_source_column).
- Comparten flag_event (shared_semantic_cue).
- Comparten group_category_level (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Pendiente.
- La historia utilizable cumplió el threshold del score. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- No se requiere acción inmediata.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_28_promoted-vs-hired-into-level_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_28_promoted-vs-hired-into-level_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_28_promoted-vs-hired-into-level_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_28_promoted-vs-hired-into-level_is-promo_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:promoted-vs-hired-into-level -->

<!-- BEGIN evaluate-attrition-variable:level -->
## Conocimiento acumulado: Level

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:37:00-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Role / job
- **Relevancia:** Level controla etapa profesional, alcance y contexto de compensación.

### Definición y fuente evaluadas

- **Definición vigente:** Nivel de puesto o management level del empleado registrado en cada snapshot mensual.
- **Tipo semántico:** grouped_mapping
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** level_grouped, job_level_primary_position, management_level
- **Grain:** Snapshot de empleado

### Relaciones con el portafolio

- Comparten group_category_level (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta validar roles de cada nivel, contradicciones detalle-grupo, valores sin mapping y cambios temporales. Resultado de la prueba: Pendiente.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta validar roles de cada nivel, contradicciones detalle-grupo, valores sin mapping y cambios temporales.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y validar roles de cada nivel, contradicciones detalle-grupo, valores sin mapping y cambios temporales; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_level-grouped_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_job-level-primary-position_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_management-level_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_level-grouped_to_job-level-primary-position_report_relationship_employee-count.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_level-grouped_to_job-level-primary-position_report_relationship_left-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_level-grouped_to_job-level-primary-position_report_relationship_right-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_level-grouped_to_job-level-primary-position_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_level-grouped_to_job-level-primary-position_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_level-grouped_to_job-level-primary-position_report_relationship_top.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_job-level-primary-position_to_management-level_report_relationship_employee-count.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_job-level-primary-position_to_management-level_report_relationship_left-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_job-level-primary-position_to_management-level_report_relationship_right-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_job-level-primary-position_to_management-level_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_job-level-primary-position_to_management-level_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_29_level_job-level-primary-position_to_management-level_report_relationship_top.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:level -->

## Aclaración de «otros / other» en la v9 — 2026-10-05

La etiqueta de la diapositiva 5 corresponde a `level_grouped=Misc`, que
aparece en el modelo congelado como categoría adicional a las siete bandas
principales. La presentación usa una descripción breve, no una definición
oficial de los puestos incluidos en `Misc`.

La consulta agregada ejecutada el 2026-10-05, sobre empleados `Employee`/
`Regular` activos de Engineering, no RF360, confirmó que **ninguna de las
37,221 personas de la foto del 2026-07-26** está en `Misc`. La categoría
aparece en la historia de julio de 2021 a julio de 2026 en una cohorte menor
de 30 empleados distintos; se suprimieron el conteo exacto y los niveles
detallados. No se atribuyen tipos concretos de puesto a esa categoría.

Fuente: `queries/audits/engineering_level_misc_detail_20261005.sql`;
evidencia y manifest: `output/analysis/engineering/20261005/20261005-080843_level-misc-clarification/`.
Esta aclaración no valida el mapping oficial, no cambia scores y no modifica
las presentaciones.
