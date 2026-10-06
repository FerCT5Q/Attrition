# Rehire

## Definición

Los campos disponibles son `is_rehire` y `rehire_date`. Para una feature time-safe, una persona cuenta como rehire únicamente cuando `rehire_date <= fis_mo_end_dt`; no debe aplicarse retrospectivamente una fecha futura a snapshots anteriores.

También debe decidirse si la feature significa:

- evento de rehire en una ventana reciente, o
- condición persistente de “alguna vez recontratado”.

## Hallazgos agregados

La auditoría cubrió 74 snapshots mensuales y encontró un cambio claro de fuente:

- prevalencia de 0.0260% el 2022-09-25;
- prevalencia de 10.3168% el 2022-10-23;
- 137 employee-months con flag pero sin fecha;
- 6 con fecha pero sin flag;
- 26 con fecha futura respecto al snapshot.

La cobertura reciente es completa, pero la serie anterior y posterior a 2022-10-23 no es directamente comparable sin armonización.

## Uso recomendado

- Tratar 2022-10-23 como límite entre eras de fuente.
- Derivar la condición desde la fecha efectiva y reconciliar excepciones del flag.
- Mantener por separado `ever_rehired` y `months_since_rehire` si ambas responden preguntas útiles.
- Validar estabilidad antes y después del cutoff antes de entrenar un modelo longitudinal.

## Attrition voluntaria observada FY2026

**Modo:** `internal_analysis` agregado. Esta evidencia actualiza el visual de Rehire, no cambia los scores v4 de la variable ni convierte la tasa en una feature predictiva.

- **Pregunta:** ¿Cuál fue la attrition voluntaria realmente observada para la población Rehire durante FY2026, usando el año disponible?
- **Motivo:** La tasa prospectiva de 12 meses por snapshot no es estimable para FY2026 porque requeriría terminaciones posteriores a esos snapshots. Una tasa realizada del año responde otra pregunta y debe llevar una etiqueta distinta.
- **Método:** Se contaron eventos `VOLUNTARY` de FY2026 atribuibles sólo a personas con un snapshot activo `is_rehire = 1` previo al evento. El denominador es el promedio mensual de headcount activo Rehire durante los snapshots FY2026.
- **Regla de aceptación:** 12 snapshots mensuales observados, al menos 30 exposiciones empleado-snapshot y 30 empleados distintos; sólo entonces publicar la tasa como observada, no prospectiva.
- **Métricas observadas (2025-10-26 a 2026-09-27):** 12 snapshots, 71,580 exposiciones empleado-snapshot, 6,934 empleados distintos, headcount mensual promedio de 5,965 y 470 salidas voluntarias. Tasa observada: **7.8793%** (7.9% mostrada).
- **Conclusión e impacto:** La tasa es publicable para FY2026 y se muestra debajo de su barra. No es comparable de manera directa con las tasas FY2024-FY2025, que son outcomes prospectivos de 12 meses posteriores al snapshot.
- **Evidencia:** `queries/audits/rehire_fy2026_observed_voluntary_attrition_20260920.sql`, ejecutada el 2026-09-20; `output/distribution/json/attrition-43-variable-distributions-v7.rehire-fy2026-observed-attrition-evidence-20260920.json`.

<!-- BEGIN evaluate-attrition-variable:rehire -->
## Conocimiento acumulado: Rehire

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:32:44-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Employment history
- **Relevancia:** Rehire distingue experiencia previa en la compañía y modifica la interpretación de tenure.

### Definición y fuente evaluadas

- **Definición vigente:** Estado de recontratación o evento fechado de rehire observable al momento del snapshot.
- **Tipo semántico:** direct_field
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** is_rehire, rehire_date
- **Grain:** Historia empleado-evento

### Relaciones con el portafolio

- Comparten flag_event (shared_semantic_cue).
- Comparten group_category_level (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: No cumple.
- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo. Resultado de la prueba: No cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Cumple parcialmente.
- La prueba aporta contexto para interpretar el concepto, pero no es un requisito definitorio y no puede elevar el score.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Aprobar la definición y confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries/audits/rehire_consistency_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_job-family_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_job-level-primary-position_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_to_job-family_report_relationship_employee-count.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_to_job-family_report_relationship_left-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_to_job-family_report_relationship_right-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_to_job-family_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_to_job-family_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_to_job-family_report_relationship_top.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_to_job-level-primary-position_report_relationship_employee-count.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_to_job-level-primary-position_report_relationship_left-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_to_job-level-primary-position_report_relationship_right-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_to_job-level-primary-position_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_to_job-level-primary-position_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_12_rehire_is-rehire_to_job-level-primary-position_report_relationship_top.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:rehire -->
