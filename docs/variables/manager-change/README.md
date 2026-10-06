# Manager change

<!-- BEGIN evaluate-attrition-variable:manager-change -->
## Conocimiento acumulado: Manager change

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:42:52-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Manager movement
- **Relevancia:** Un cambio reciente de manager puede representar disrupción organizacional.

### Definición y fuente evaluadas

- **Definición vigente:** El empleado tuvo un cambio de manager efectivo dentro de la ventana aprobada.
- **Tipo semántico:** direct_field
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** manager_change, manager_change_date
- **Grain:** Empleado-evento

### Relaciones con el portafolio

- El conteo histórico depende de una definición time-safe y observable del evento Manager change.
- Number of manager changes depende de Manager change.
- Major inflection points depende de Manager change.
- Comparten manager_change (shared_source_column).
- Comparten manager_change_date (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten flag_event (shared_semantic_cue).
- Comparten manager_team_layers (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_39_manager-change_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_39_manager-change_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_39_manager-change_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_39_manager-change_manager-change_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:manager-change -->
