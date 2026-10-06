# High turnover under this person

<!-- BEGIN evaluate-attrition-variable:high-turnover-under-this-person -->
## Conocimiento acumulado: High turnover under this person

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:41:37-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Manager risk
- **Relevancia:** La rotación histórica del equipo puede representar presión local de retención.

### Definición y fuente evaluadas

- **Definición vigente:** El equipo del manager supera un umbral aprobado de rotación durante una ventana histórica.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** manager_employee_id, employee_id, is_termed, term_date, term_type
- **Grain:** Manager / equipo

### Relaciones con el portafolio

- Las señales de riesgo del manager dependen de una definición gobernada de rotación histórica del equipo.
- High turnover under this person depende de Team turnover.
- Comparten employee_id (shared_source_column).
- Comparten is_termed (shared_source_column).
- Comparten manager_employee_id (shared_source_column).
- Comparten term_date (shared_source_column).
- Comparten term_type (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten flag_event (shared_semantic_cue).
- Comparten manager_team_layers (shared_semantic_cue).
- Comparten ratio_rate_percent (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 99.998%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Pendiente.
- La historia utilizable cumplió el threshold del score. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- No se requiere acción inmediata.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_37_high-turnover-under-this-person_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_37_high-turnover-under-this-person_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_37_high-turnover-under-this-person_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_37_high-turnover-under-this-person_is-termed_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_37_high-turnover-under-this-person_term-type_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:high-turnover-under-this-person -->
