# Transfer within past year

<!-- BEGIN evaluate-attrition-variable:transfer-within-past-year -->
## Conocimiento acumulado: Transfer within past year

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:27:19-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Applications / internal mobility
- **Relevancia:** Una movilidad interna reciente puede modificar el riesgo de salida después del cambio.

### Definición y fuente evaluadas

- **Definición vigente:** El empleado tuvo una transferencia efectiva durante los 12 meses previos a cada snapshot.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** is_transferred, transfer_date
- **Grain:** Empleado-evento

### Relaciones con el portafolio

- Major inflection points depende de Transfer within past year.
- Comparten is_transferred (shared_source_column).
- Comparten transfer_date (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten flag_event (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_03_transfer-within-past-year_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_03_transfer-within-past-year_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_03_transfer-within-past-year_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_03_transfer-within-past-year_is-transferred_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:transfer-within-past-year -->
