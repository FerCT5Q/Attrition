# Job family

## Campos

| Campo | Significado práctico | Cardinalidad observada |
|---|---|---:|
| `job_family` | Familia de trabajo detallada; distingue especialidades y funciones concretas. | 288 |
| `job_family_group` | Agrupación amplia de familias relacionadas. | 15 |

La auditoría agregada del 10 de agosto de 2026 encontró ambos campos poblados para los 50,043 empleados regulares activos del corte. El profile validado posteriormente mantuvo 100% de cobertura reciente y 72 meses de historia utilizable.

## Relación entre ambos

`job_family_group` resume a `job_family`: muchas familias detalladas pertenecen al mismo grupo. No son dos mediciones independientes. Por ejemplo, varias especialidades de ingeniería pueden compartir un grupo general de Engineering aunque conserven familias distintas.

## Uso recomendado en attrition

- Usar `job_family_group` para dashboards, cohortes amplias y comparaciones ejecutivas.
- Usar `job_family` como feature más detallada cuando el tamaño del grupo sea suficiente.
- Aplicar mínimos de población antes de mostrar una familia detallada.
- No interpretar una diferencia entre familias como causalidad; puede reflejar nivel, país, organización o tenure.

## Limitaciones

- La cardinalidad detallada aumenta el riesgo de grupos pequeños.
- Se debe comprobar estabilidad de mappings cuando cambien familias o estructuras organizacionales.
- El modelo debe utilizar el valor del snapshot, no la clasificación actual aplicada hacia atrás.

## Auditoría enfocada del mapping — 17 de agosto de 2026

Se revalidó `Job family` como `grouped_mapping` para empleados regulares activos,
con grain empleado-snapshot y snapshots cerrados entre 2020-07-26 y 2026-07-26.
La fecha de ejecución fue 2026-08-17 y el límite de consulta excluyó fechas
posteriores a ese día.

### Hallazgos agregados

- Se reconciliaron 2,973,166 filas y 2,973,166 llaves empleado-snapshot.
- Cada llave tuvo exactamente una fila: cero duplicados, llaves nulas o valores
  contradictorios de familia/grupo.
- Se observaron 343 familias y 16 grupos; todas las filas tuvieron tanto
  `job_family` como `job_family_group`.
- Ninguna familia perteneció a más de un grupo dentro del mismo snapshot.
- Cinco familias cambiaron de grupo durante el periodo. Los cinco cambios
  ocurrieron con la cadencia esperada, permanecieron estables en los tres
  snapshots siguientes y no revirtieron. Esto es compatible con
  recategorizaciones efectivas, pero no demuestra su aprobación de negocio.
- No se detectaron etiquetas candidatas a `Unknown`, `Other` o `Unassigned`
  mediante la regla agregada definida antes de la ejecución.
- Se identificaron 51 familias históricas no observadas durante los últimos 12
  meses del periodo y cinco familias nuevas en esos 12 meses. Son candidatos
  operativos a categorías retiradas/nuevas, no un estatus oficial de vigencia.
- `job_family_group_short` faltó en 363 filas, distribuidas en 44 snapshots y un
  grupo; la última ocurrencia fue 2025-01-26. Los campos principales
  `job_family` y `job_family_group` permanecieron completos.
- La búsqueda de metadata encontró 300 instancias de las cuatro columnas en 96
  tablas de `hrda`, pero cero comentarios de columna. Redshift no aporta una
  definición oficial ni una tabla de vigencias identificable mediante esta
  metadata.

### Decisión de evidencia

Los datos confirman una relación muchos-a-uno consistente dentro de cada
snapshot y una llave empleado-fecha reproducible. No confirman por sí solos la
semántica oficial, la autoridad del mapping ni el motivo aprobado de las cinco
recategorizaciones. Por esa razón, `Definition` debe permanecer como máximo en
1 hasta obtener lineage o una definición gobernada del sistema propietario. La
evidencia de grain y unicidad puede utilizarse para reevaluar `Join` en un nuevo
assessment v4, pero no modifica retroactivamente el run publicado.

### SQL trazable

- `queries/audits/job_family_definition_metadata_20260817.sql`
- `queries/audits/job_family_lineage_metadata_summary_20260817.sql`
- `queries/audits/job_family_mapping_reconciliation_20260817.sql`
- `queries/audits/job_family_mapping_yearly_20260817.sql`
- `queries/audits/job_family_mapping_change_stability_20260817.sql`

<!-- BEGIN evaluate-attrition-variable:job-family -->
## Conocimiento acumulado: Job family

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:30:02-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Role / job
- **Relevancia:** La familia detallada aporta contexto ocupacional y el grupo permite segmentos más amplios.

### Definición y fuente evaluadas

- **Definición vigente:** Job family detallada y agrupada registradas para cada empleado activo en el snapshot.
- **Tipo semántico:** grouped_mapping
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** job_family, job_family_group
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

- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family-group_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family-short_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family-group-short_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_to_job-family-short_report_relationship_employee-count.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_to_job-family-short_report_relationship_left-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_to_job-family-short_report_relationship_right-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_to_job-family-short_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_to_job-family-short_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_to_job-family-short_report_relationship_top.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family-group_to_job-family-group-short_report_relationship_employee-count.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family-group_to_job-family-group-short_report_relationship_left-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family-group_to_job-family-group-short_report_relationship_right-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family-group_to_job-family-group-short_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family-group_to_job-family-group-short_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family-group_to_job-family-group-short_report_relationship_top.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_to_job-family-group_report_relationship_employee-count.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_to_job-family-group_report_relationship_left-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_to_job-family-group_report_relationship_right-distinct-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_to_job-family-group_report_relationship_left-values-with-multiple-right-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_to_job-family-group_report_relationship_right-values-with-multiple-left-values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_07_job-family_job-family_to_job-family-group_report_relationship_top.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:job-family -->
