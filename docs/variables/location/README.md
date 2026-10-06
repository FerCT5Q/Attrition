# Location

<!-- BEGIN evaluate-attrition-variable:location -->
## Conocimiento acumulado: Location

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:28:05-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Location / workplace
- **Relevancia:** La geografía laboral permite segmentar por mercado de trabajo, sitio y contexto operativo.

### Definición y fuente evaluadas

- **Definición vigente:** País de trabajo y sitio de oficina del empleado en cada snapshot mensual.
- **Tipo semántico:** direct_field
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** country, office_site
- **Grain:** Snapshot de empleado

### Relaciones con el portafolio

- Hours away from manager depende de Location.
- Comparten country (shared_source_column).
- Comparten office_site (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten group_category_level (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 95.5034%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo. Resultado de la prueba: Pendiente.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Pendiente.
- Coverage reciente cumplió el threshold del score. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- No se requiere acción inmediata.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_04_location_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_04_location_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_04_location_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_04_location_country_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_04_location_office-site_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_04_location_country_to_office-site_report_relationship_employee-count.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_04_location_country_to_office-site_report_relationship_left-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_04_location_country_to_office-site_report_relationship_right-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_04_location_country_to_office-site_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_04_location_country_to_office-site_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_04_location_country_to_office-site_report_relationship_top.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:location -->
