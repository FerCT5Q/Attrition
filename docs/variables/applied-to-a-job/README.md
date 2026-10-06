# Applied to a job

<!-- BEGIN evaluate-attrition-variable:applied-to-a-job -->
## Conocimiento acumulado: Applied to a job

_Assessment formal v4: `attrition-43-monthly-fiscal-20260816` (2026-08-16T20:25:48-06:00). Fuente de distribución revalidada en la ejecución versionada del 2026-09-13; la referencia previa es del 2026-09-10._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Applications / internal mobility
- **Relevancia:** La búsqueda interna reciente puede señalar intención de movilidad o riesgo de salida.

### Definición y fuente evaluadas

- **Definición vigente:** El empleado tuvo al menos una solicitud interna de empleo deduplicada durante el mes anterior.
- **Tipo semántico:** derived_feature
- **Tabla / fuente del assessment histórico:** hrda.applications
- **Columnas:** employee_id, candidate_id, cand_applied, application_date, req_id
- **Grain:** Empleado-evento

### Relaciones con el portafolio

- More than 3 job applications depende de Applied to a job.
- Comparten application_date (shared_source_column).
- Comparten cand_applied (shared_source_column).
- Comparten candidate_id (shared_source_column).
- Comparten employee_id (shared_source_column).
- Comparten req_id (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten flag_event (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (9 puntos).
- **Scores:** Source=2, Definition=1, Coverage=1, Missingness=1, Consistency=1, History=1, Join=1, Effort=1
- **Coverage reciente:** 79.1847%.
- **Historia utilizable:** 31.0 meses.

**Hallazgos principales**

- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Pendiente.
- Existen eventos históricos, pero el feed no llega al periodo actual de scoring. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- El coverage observable reciente está por debajo del umbral de 95% para score 2.
- Missingness reciente supera el máximo de 5% para score 2.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.

**Acciones recomendadas**

- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Restablecer y validar el feed vigente y después repetir el perfil longitudinal.
- Resolver brechas de elegibilidad u observabilidad y repetir el perfil; objetivo >= 95%.
- Investigar brechas por fecha y segmento elegible; objetivo <= 5% sin patrón sistemático.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_01_applied-to-a-job_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
## Revalidación de fuente para la distribución — 2026-09-10

Esta revalidación actualiza solamente la evidencia descriptiva usada en la lámina de distribución. No reemite el scorecard v4 ni modifica los scores históricos: Coverage, Missingness, Consistency y Join requieren un perfil nuevo en el grain empleado-snapshot.

- **Fuente usada en la distribución actualizada:** `hrda.job_applications_vw`.
- **Filtros y grain:** `cand_applied=1`, `employee_id`, `req_id` y `application_date` no nulos; solicitante-año fiscal; deduplicación por `employee_id + fiscal_year + req_id`.
- **Historia observada:** 14,422 eventos deduplicados, desde 2020-07-13 hasta 2026-09-10.
- **Puente fiscal:** los 14,422 eventos se asignaron exactamente a un año fiscal; sin eventos sin mapeo ni con mapeo múltiple.
- **Reconciliación con la fuente histórica:** los 9,903 eventos de `hrda.applications` aparecen en la nueva vista dentro de la ventana común; la vista contiene 936 eventos adicionales. La coincidencia nueva→vieja es 91.3645%, por lo que columnas equivalentes no prueban por sí solas el mismo lineage o scope de negocio.
- **Ventana de presentación estándar:** FY2022–FY2024. FY2025 es un año completo pero se suprime porque dos buckets 1/2/3/4+ no alcanzan `n >= 30`; FY2026 está parcial al corte de la fuente.

### Ventana de revisión interna autorizada

La ventana de presentación estándar conserva FY2022–FY2024 y suprime FY2025
cuando algún bucket no alcanza `n >= 30`. Para la revisión interna con Julia,
ambos desarrolladores del proyecto, FY2025 y FY2026 YTD también se muestran
como conteos agregados exploratorios aunque algún bucket sea menor de `n=30`.
Esta excepción no habilita filas, requisiciones, nombres, acceso de managers,
cambios en score v4 ni producción.

### Limitaciones y acción

- La distribución describe solicitantes vinculados, no una tasa de la plantilla; no demuestra ceros de solicitud ni valor predictivo.
- Las filas sin `employee_id` no pueden convertirse en una feature por empleado.
- Antes de modificar la definición de la feature o adoptar los buckets `0 / 1 / 2+`, confirmar con el owner el lineage y scope de `hrda.job_applications_vw`, y ejecutar la reconciliación empleado-snapshot con controles de temporalidad y leakage.

### SQL y evidencia de la revalidación

- `queries/audits/application_intensity_job_applications_vw_fiscal_year_mapping_20260910.sql`
- `queries/profiles/application_intensity_job_applications_vw_distinct_applicant_fiscal_year_20260910.sql`
- `queries/audits/application_intensity_job_applications_vw_publishability_20260910.sql`
- `queries/audits/applied_to_a_job_source_reconciliation_20260910.sql`
- `queries/profiles/job_applications_vw_recent_event_profile_20260910.sql`

## Ejecución versionada de evidencia — 2026-09-13

Esta ejecución actualiza la evidencia descriptiva de la presentación usando `hrda.job_applications_vw`. No cambia el score v4, el catálogo de variables ni las decisiones de producción. La vista se trata como una fuente ampliada: no se asume que tenga el mismo lineage o scope de negocio que `hrda.applications`.

### Autorización interna de colaboración — 2026-09-13

Por instrucción explícita del solicitante, la vista anual de intensidad se
clasifica como `internal_analysis` para compartirla únicamente entre el
solicitante y Julia, ambos desarrolladores del proyecto. La autorización está
registrada en
`config/application_intensity_internal_analysis_authorization_20260913.json`.

La excepción permite revisar conteos agregados menores de 30 en los buckets
`1 / 2 / 3 / 4+` de FY2025 y FY2026 YTD. No permite guardar filas, IDs, nombres,
requisiciones, títulos de vacantes ni datos individuales; tampoco permite
redistribución, acceso de managers, uso operativo, cambio de score v4 o
adopción en producción. FY2026 sigue marcado como parcial.

### Distribución anual de intensidad

- **Corte de datos:** 2026-09-10; `cand_applied=1`; `employee_id`, `req_id` y `application_date` no nulos; fechas de aplicación no posteriores al corte.
- **Grain y deduplicación:** solicitante–periodo fiscal, con requisiciones únicas por `employee_id + fiscal period + req_id`.
- **Calidad de eventos:** 74,993 filas calificadas se reducen a 14,428 claves de evento únicas; 60,565 filas duplicadas quedan identificadas como diagnóstico. La vista contiene 8,496 empleados vinculados y 6,277 requisiciones vinculadas.
- **Reconciliación fiscal:** 14,428 claves se asignan exactamente a un año fiscal; no hay eventos sin mapeo, multi-mapeo ni discrepancias de totales.
- **Publicación estándar:** FY2022–FY2024 cumplen `n >= 30` en los cuatro buckets `1 / 2 / 3 / 4+`. Bajo la autorización interna registrada, FY2025 y FY2026 YTD se muestran como evidencia exploratoria agregada aunque dos buckets de cada periodo están por debajo de `n=30`; no son filas publicables para presentación. FY2026 YTD through 2026-09-10 es parcial y no comparable con años fiscales completos.
- **Deriva frente a la referencia congelada del 2026-09-10:** la comparación actual conserva 9,903 eventos antiguos y añade 937 eventos nuevos en la ventana común; old→new = 100% y new→old = 91.3561%. La referencia congelada registraba 936 adicionales y 91.3645% new→old. Esta diferencia es un diagnóstico de refresco de fuente, no una modificación de la afirmación histórica de la presentación.

### Distribución propuesta por empleado–snapshot

- **Población y grain:** empleados regulares activos (`worker_type='Employee'`, `employee_type='Regular'`, `active_status=1`) en cada snapshot mensual; una observación por empleado–snapshot.
- **Ventana:** `(snapshot - 6 meses, snapshot]`.
- **Clasificación:** `0` sólo cuando hay cero requisiciones únicas y la cobertura del feed permite distinguir cero de ausencia; `1` para exactamente una requisición; `2+` para dos o más; `Unknown` cuando no se puede confirmar el cero. No se imputan ceros a empleados sin cobertura demostrada.
- **Controles:** 68 snapshots revisados; no hay filas duplicadas de snapshot, aplicaciones posteriores al snapshot incluidas ni discrepancias en la reconciliación independiente de conteos. El join agregado reporta 2,836,981 employee-snapshots elegibles y 4.6741% de cobertura time-safe global; la cobertura puede variar por fecha.
- **Publicación reciente:** el último snapshot disponible es 2026-08-23, pero se suprime porque su bucket `2+` queda por debajo de `n=30`. El último snapshot completamente publicable es 2026-07-26: denominador 49,652, `0=3,935` (7.9252%), `1=843` (1.6978%), `2+=30` (0.0604%) y `Unknown=44,844` (90.3166%). De los últimos 12 snapshots mensuales completos, sólo uno supera la puerta de publicación de los cuatro buckets.
- **Interpretación:** esta lámina es evidencia exploratoria descriptiva, no una feature aprobada ni una predicción individual; requiere aprobación de lineage y una revalidación formal antes de adoptar la definición en producción.

### Trazabilidad de la ejecución

- **Evidencia anual:** `output/distribution/json/attrition-43-variable-distributions-v2.application-intensity-evidence-20260913.json`
- **Evidencia employee–snapshot:** `output/distribution/json/attrition-43-variable-distributions-v2.application-employee-snapshot-trailing-6m-evidence-20260913.json`
- **Manifest:** `output/distribution/json/attrition-43-variable-distributions-v2-manifest.json` (transición de 50 a 51 láminas; artefactos históricos de 2026-09-08 y 2026-09-10 preservados).
- **Consultas de metadata y calidad:** `queries/audits/application_job_applications_vw_metadata_20260913.sql`, `queries/audits/application_job_applications_vw_event_quality_20260913.sql`
- **Reconciliación de fuente y fiscal:** `queries/audits/applied_to_a_job_source_reconciliation_20260913.sql`, `queries/audits/application_employee_snapshot_trailing_6m_fiscal_reconciliation_20260913.sql`
- **Join, temporalidad y publicación rolling:** `queries/audits/application_employee_snapshot_trailing_6m_join_20260913.sql`, `queries/audits/application_employee_snapshot_trailing_6m_temporal_20260913.sql`, `queries/audits/application_employee_snapshot_trailing_6m_publishability_20260913.sql`
- **Perfiles de presentación:** `queries/profiles/application_intensity_job_applications_vw_annual_with_ytd_20260913.sql`, `queries/profiles/application_employee_snapshot_trailing_6m_distribution_20260913.sql`

<!-- END evaluate-attrition-variable:applied-to-a-job -->
