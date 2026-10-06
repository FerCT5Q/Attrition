# Number of manager changes

## Vista exploratoria de distribución — 2026-09-09

Para responder la pregunta de distribución, se congeló una vista descriptiva con un supuesto explícito: usar el corte mensual del deck (`2026-08-23`) y contar los eventos con fecha `manager_change_date` dentro de los seis meses anteriores, `(2026-02-23, 2026-08-23]`. Un evento requiere `manager_change=1`; las observaciones mensuales repetidas del mismo empleado y fecha de evento cuentan una sola vez.

La población agregada fue de **50,043 empleados regulares activos** con llave utilizable. La distribución observada fue: **0 cambios: 41,266 (82.46%)**, **1 cambio: 7,528 (15.04%)**, **2 cambios: 1,138 (2.27%)** y **3 o más: 111 (0.22%)**. Los buckets suman la población completa y todos cumplen `n >= 30`.

La consulta reportó 10,317 llaves de evento distintas en la ventana, cero observaciones repetidas adicionales, cero flags positivos sin fecha y cero flags fuera de `0/1`. Esto habilita una visual descriptiva del supuesto, pero no confirma todavía la feature final: siguen pendientes la aprobación de la ventana para modelado, reglas de reset por reingreso/rol y la semántica definitiva del acumulado. La evidencia agregada está en `output/distribution/json/number-of-manager-changes-distribution-6m-evidence-20260909.json` y la consulta en `queries/profiles/number_of_manager_changes_distribution_6m_20260909.sql`.

## Comparación anual suplementaria — 2026-09-09

La ventana seleccionada para la señal principal se conserva en seis meses. Para
responder la pregunta de si es común que un empleado cambie dos veces de
manager en un año, se calculó una segunda distribución con la misma población
y corte mensual, pero con la ventana `(2025-08-23, 2026-08-23]`.

El resultado anual fue: **0 cambios: 36,628 (73.19%)**, **1 cambio: 10,801
(21.58%)**, **2 cambios: 2,260 (4.52%)** y **3 o más: 354 (0.71%)**. Por lo
tanto, dos cambios anuales no describen a la mayoría de la población, pero sí
son una cohorte agregada publicable y visible. Las cuatro categorías cumplen
`n >= 30` y suman los 50,043 empleados regulares activos del corte.

La consulta verificó cero observaciones repetidas adicionales, cero flags
positivos sin fecha, cero flags fuera de `0/1` y cero empleados cuyo conteo
anual fuera menor que el conteo semestral anidado. Esta comparación es
descriptiva y suplementaria: no sustituye la ventana de seis meses, ni resuelve
las reglas pendientes de reset o la semántica final de la feature de modelo.

**Evidencia trazable:**

- `config/number_of_manager_changes_distribution_plan_v5_20260909.yaml`
- `queries/profiles/number_of_manager_changes_distribution_12m_20260909.sql`
- `output/distribution/json/number-of-manager-changes-distribution-12m-evidence-20260909.json`

## Sensibilidad: excluir movilidad formal en la misma fecha — 2026-09-14

La distribución primaria conserva todos los cambios de manager. Para validar la
propuesta de no mezclar los cambios asociados a movilidad formal, se comparó
una alternativa que excluye un evento sólo si existe, para la misma persona y
la misma fecha efectiva, una transferencia o promoción con flag positivo. No se
excluyen transferencias o promociones ocurridas en otro día de la ventana.

En seis meses, **538 de 10,317 eventos (5.22%)** coincidieron con esa regla;
el bucket de cero cambios pasó de **82.46% (41,266)** a **83.27% (41,671)**.
En doce meses, la coincidencia fue **913 de 17,013 eventos (5.37%)**; el bucket
de cero cambios pasó de **73.19% (36,628)** a **74.29% (37,178)**. Las cuatro
distribuciones reconcilian con 50,043 empleados regulares activos, todos los
buckets publicados cumplen `n >= 30`, no hubo flags positivos sin fecha y el
conteo anual nunca fue menor que el semestral.

La comparación es una sensibilidad descriptiva y no modifica la señal primaria,
su score ni su definición de modelo. Una coincidencia técnica no determina si
la movilidad formal debe excluirse, etiquetarse en otra feature o modelarse como
predictor independiente; esa decisión requiere alineación funcional y una
evaluación longitudinal posterior.

**Evidencia trazable:**

- `config/number_of_manager_changes_distribution_plan_v7_20260914.yaml`
- `queries/profiles/number_of_manager_changes_same_date_mobility_comparison_20260914.sql`
- `output/distribution/json/number-of-manager-changes-same-date-mobility-comparison-evidence-20260914.json`

<!-- BEGIN evaluate-attrition-variable:number-of-manager-changes -->
## Conocimiento acumulado: Number of manager changes

_Actualizado por el assessment v4 `number-of-manager-changes-join-validation-20260820-4` el 2026-08-20T20:54:09-06:00._

### Contexto del problema

- **Problema:** Revalidar el Join de Number of manager changes para determinar si los eventos de cambio de manager pueden asociarse de forma única, completa y time-safe a cada snapshot mensual del empleado.
- **Decisión / caso de uso:** Decidir si el criterio Join puede subir de 1 a 2 sin asumir todavía una ventana definitiva para el conteo histórico.
- **Outcome:** Attrition voluntario ocurrido después del snapshot mensual de predicción y antes del siguiente snapshot.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Para cada snapshot sólo pueden utilizarse eventos con fecha efectiva anterior o igual al cierre del snapshot; nunca se enlazan cambios futuros.
- **Rol de la variable:** Manager movement
- **Relevancia:** El conteo sólo es utilizable si la historia de eventos se une sin duplicados, pérdidas ni información futura.

### Definición y fuente evaluadas

- **Definición vigente:** Conteo time-safe de eventos deduplicados de cambio de manager por empleado-snapshot.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** employee_id, fis_mo_beg_dt, fis_mo_end_dt, worker_type, employee_type, active_status, manager_change, manager_change_date
- **Grain:** Conteo móvil de eventos por empleado-snapshot

### Relaciones con el portafolio

- No se documentaron relaciones contextuales adicionales.

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (13 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=2, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- La prueba aporta contexto para interpretar el concepto, pero no es un requisito definitorio y no puede elevar el score.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- No se requiere acción inmediata; repetir la validación si cambia la fuente o definición.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_coverage.sql`
- `queries/audits/number_of_manager_changes_source_access_20260820.sql`
- `queries/audits/number_of_manager_changes_join_reconciliation_v2_20260820.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_report_metadata.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_report_column_profile.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_manager-change_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_top.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_top.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_top.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_top.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_top.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 4.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:number-of-manager-changes -->

<!-- BEGIN evaluate-attrition-variable-run:number-of-manager-changes:number-of-manager-changes-join-validation-20260820-3 -->

### Historial de decisión — run `number-of-manager-changes-join-validation-20260820-3`

_Registrado el 2026-08-20T20:24:32-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Media - utilizable con trabajo (12 puntos).

**Evolución del plan**

- Plan v3: El runner rechazó la narrativa pública de dos reglas porque estaba dominada por identificadores técnicos. Esta versión conserva las mismas consultas y umbrales, pero explica completamente en español qué significa aprobar cada prueba.

**Validaciones y efecto observado**

- **source:** ¿Existen todos los campos necesarios para la reconstrucción segura en el tiempo? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Cada evento tiene una primera observación válida y libre de información futura? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El evento y su primera observación encuentran exactamente un snapshot del mismo empleado? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿La derivación devuelve exactamente una fila para cada empleado-snapshot elegible? — resultado No cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Esta validación decide la longitud final de la ventana retrospectiva? — resultado Informativa; impacto: Evidencia contextual para Definition; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_coverage.sql`
- `queries/audits/number_of_manager_changes_source_access_20260820.sql`
- `queries/audits/number_of_manager_changes_join_reconciliation_v2_20260820.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_report_metadata.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_report_column_profile.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-beg-dt_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-end-dt_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_worker-type_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_employee-type_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_active-status_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_manager-change_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_top.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_top.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_top.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_top.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-3_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_top.sql`

<!-- END evaluate-attrition-variable-run:number-of-manager-changes:number-of-manager-changes-join-validation-20260820-3 -->

<!-- BEGIN evaluate-attrition-variable-run:number-of-manager-changes:number-of-manager-changes-join-validation-20260820-4 -->

### Historial de decisión — run `number-of-manager-changes-join-validation-20260820-4`

_Registrado el 2026-08-20T20:54:09-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Media - utilizable con trabajo (13 puntos).

**Evolución del plan**

- Plan v4: Redshift devolvió las tasas decimales como texto y el motor no pudo evaluarlas, aunque todos los conteos de correspondencia fueron válidos. Esta versión conserva la misma evidencia y usa los conteos requeridos por el contrato de Join, que son numéricos y determinan directamente si existen pérdidas o multiplicaciones.

**Validaciones y efecto observado**

- **source:** ¿Existen todos los campos necesarios para la reconstrucción segura en el tiempo? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Cada evento tiene una primera observación válida y libre de información futura? — resultado Cumple; impacto: Join quedó en 2 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El evento y su primera observación encuentran exactamente un snapshot del mismo empleado? — resultado Cumple; impacto: Join quedó en 2 de acuerdo con la evidencia y los límites v4.
- **join:** ¿La derivación devuelve exactamente una fila para cada empleado-snapshot elegible? — resultado Cumple; impacto: Join quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Esta validación decide la longitud final de la ventana retrospectiva? — resultado Informativa; impacto: Evidencia contextual para Definition; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_coverage.sql`
- `queries/audits/number_of_manager_changes_source_access_20260820.sql`
- `queries/audits/number_of_manager_changes_join_reconciliation_v2_20260820.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_report_metadata.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_report_column_profile.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_manager-change_report_top_values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-beg-dt_to_fis-mo-end-dt_report_relationship_top.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_fis-mo-end-dt_to_worker-type_report_relationship_top.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_worker-type_to_employee-type_report_relationship_top.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_employee-type_to_active-status_report_relationship_top.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_employee-count.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_left-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_right-distinct-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\number-of-manager-changes-join-validation-20260820-4_01_number-of-manager-changes_active-status_to_manager-change_report_relationship_top.sql`

<!-- END evaluate-attrition-variable-run:number-of-manager-changes:number-of-manager-changes-join-validation-20260820-4 -->
