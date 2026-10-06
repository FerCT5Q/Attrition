# Engineering vs. non-engineering

<!-- BEGIN evaluate-attrition-variable:engineering-vs-non-engineering -->
## Conocimiento acumulado: Engineering vs. non-engineering

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:31:56-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Role / job
- **Relevancia:** El segmento controla diferencias materiales entre mercados laborales técnicos y no técnicos.

### Definición y fuente evaluadas

- **Definición vigente:** Clasificación de ingeniería frente a no ingeniería para cada empleado en el snapshot.
- **Tipo semántico:** grouped_mapping
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** eng_or_noneng
- **Grain:** Snapshot de empleado

### Relaciones con el portafolio

- Comparten group_category_level (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta validar roles de cada nivel, contradicciones detalle-grupo, valores sin mapping y cambios temporales.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Aprobar la definición y validar roles de cada nivel, contradicciones detalle-grupo, valores sin mapping y cambios temporales; guardar SQL agregado, regla previa y métricas de reconciliación.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_11_engineering-vs-non-engineering_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_11_engineering-vs-non-engineering_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_11_engineering-vs-non-engineering_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_11_engineering-vs-non-engineering_eng-or-noneng_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:engineering-vs-non-engineering -->
