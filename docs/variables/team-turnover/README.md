# Team turnover

## Uso como componente de High risk manager (2026-08-21)

`Team turnover` aporta la base de salidas observadas y empleado-meses de
exposición. La metodología acordada para `High risk manager` no utiliza esta
tasa de forma aislada: compara salidas voluntarias observadas contra salidas
esperadas para equipos comparables, aplica shrinkage para equipos pequeños y
exige persistencia temporal.

La definición completa, los parámetros iniciales y las validaciones pendientes
se mantienen en [High risk manager](../high-risk-manager/README.md). Esta
relación es contexto de diseño y no modifica los scores históricos de ninguna
de las dos variables.

## Escenarios descriptivos de seis meses (2026-09-08)

Se acordó una definición operacional para una visualización interna, sin
etiquetar ni evaluar a managers individuales. En un snapshot `t`, el equipo
directo de un manager `m` contiene exclusivamente empleados regulares activos
`e` para los que `manager_employee_id(e, t) = m`. El manager y sus pares no
pertenecen al denominador de su propio equipo.

Para el corte mensual `2026-08-23`, la ventana es
`(2026-02-23, 2026-08-23]`, con seis snapshots mensuales. Una salida se
atribuye al último `manager_employee_id` observado para la persona en un
snapshot activo-regular cerrado no posterior a `term_date`.

- **Escenario A:** todo manager con al menos un reporte directo activo en el
  corte.
- **Escenario B:** solo managers con más de cinco reportes directos en el
  corte (seis o más).
- **Numerador:** `term_type = 'Voluntary'` exclusivamente. `Voluntary
  Exception` se excluye hasta que HR confirme su tratamiento.
- **Métrica publicada:** salidas voluntarias por 100 empleado-meses de
  reportes directos y su equivalente porcentual a seis meses. Es descriptiva,
  agregada y no causal.

### Evidencia agregada

- Los 50,214 empleados regulares activos del snapshot diario 2026-09-07
  tuvieron una fila por empleado; las 50,213 referencias no nulas de manager
  resolvieron una sola vez contra el directorio activo completo.
- En la ventana mensual hubo 1,671 terminaciones con `term_type = 'Voluntary'`;
  1,587 (94.97%) encontraron un manager previo y las no atribuibles se
  excluyeron.
- El escenario A contiene 10,583 equipos y el B 3,256; ambos superan el
  mínimo publicable de 30 equipos.

### Limitaciones y siguiente uso

La exclusión de 84 salidas sin manager previo, la falta de clasificación de
`Voluntary Exception`, y la ausencia de shrinkage o ajuste por composición
impiden usar esta tasa como label o ranking de managers. Puede mostrarse como
comparación exploratoria agregada y servir como base para una feature posterior
si se versionan esas reglas.

### SQL trazable

- `queries/profiles/team_turnover_6m_scenarios_20260908.sql`
- `queries/audits/team_turnover_voluntary_term_type_domain_20260908.sql`
- `queries/audits/team_turnover_direct_team_membership_20260908.sql`
- `queries/audits/team_turnover_manager_reference_resolution_20260908.sql`

<!-- BEGIN evaluate-attrition-variable:team-turnover -->
## Conocimiento acumulado: Team turnover

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:28:35-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Turnover contagion
- **Relevancia:** La rotación reciente del equipo puede reflejar inestabilidad local relacionada con attrition.

### Definición y fuente evaluadas

- **Definición vigente:** Tasa rezagada de rotación del equipo calculada sólo con terminaciones conocidas en cada snapshot.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** manager_employee_id, employee_id, is_termed, term_date, term_type
- **Grain:** Contexto equipo / empleado

### Relaciones con el portafolio

- Las señales de riesgo del manager dependen de una definición gobernada de rotación histórica del equipo.
- More than 1 employee leaves in a year depende de Team turnover.
- High risk manager depende de Team turnover.
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

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 99.998%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

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

- `queries\profiles\attrition-43-monthly-fiscal-20260816_05_team-turnover_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_05_team-turnover_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_05_team-turnover_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_05_team-turnover_is-termed_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_05_team-turnover_term-type_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:team-turnover -->
