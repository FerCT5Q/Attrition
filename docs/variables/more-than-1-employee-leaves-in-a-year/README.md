# More than 1 employee leaves in a year

<!-- BEGIN evaluate-attrition-variable:more-than-1-employee-leaves-in-a-year -->
## Conocimiento acumulado: More than 1 employee leaves in a year

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:29:04-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Turnover contagion
- **Relevancia:** La concentración de salidas puede representar exposición a pérdidas repetidas dentro del equipo.

### Definición y fuente evaluadas

- **Definición vigente:** El equipo del manager tuvo más de una terminación elegible durante los 12 meses previos al snapshot.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** manager_employee_id, employee_id, is_termed, term_date, term_type
- **Grain:** Contexto equipo / empleado

## Revalidación 2026-09-08: definición formal aprobada para cálculo

La variable se define como una `derived_feature` time-safe en el grain
`manager-team × employee snapshot`:

- **Equipo:** `Team(m,t)` contiene los empleados `worker_type='Employee'`,
  `employee_type='Regular'` y `active_status=1` observados en el snapshot `t`
  cuyo `manager_employee_id` es `m`. El manager no se agrega a su propio
  equipo directo. Una persona puede ser reporte directo de otro manager y,
  simultáneamente, liderar su propio equipo.
- **Pares:** son las personas que comparten el mismo manager superior que el
  manager focal, excluyendo al manager focal. Esta relación sirve para
  describir la estructura, pero no entra en el numerador de la variable.
- **Salida elegible:** un evento distinto por empleado y `term_date` cuyo
  `term_type` sea exactamente `Voluntary`. Se excluyen `Involuntary`,
  `Voluntary Exception`, nulos y fechas posteriores al snapshot.
- **Ventana:** `(t - 6 meses, t]`, con seis snapshots mensuales completos.
- **Bandera:** vale `1` cuando el equipo tiene al menos dos salidas voluntarias
  distintas en la ventana; en otro caso vale `0`. Para lectura descriptiva se
  publican los buckets `0`, `1` y `2+`.

La comprobación agregada del ejemplo focal confirmó que la persona focal,
su manager y los cuatro reportes directos esperados convergen en el mismo
equipo directo; también coincidieron la cadena manager–manager y la relación
de pares en los snapshots diario y mensual revisados. Los identificadores y
los nombres se mantuvieron únicamente dentro de la consulta y no se publican.

Se conservaron dos atribuciones para hacer explícito el efecto de los cambios
de manager:

1. **Principal (`manager_at_exit`):** atribuye la salida al último manager no
   nulo observado para la persona en un snapshot igual o anterior a
   `term_date`.
2. **Sensibilidad (`manager_at_evaluation`):** atribuye la salida al último
   manager no nulo disponible hasta el snapshot de evaluación `t`.

La población evaluada llega hasta `2026-08-23` y contiene 40 snapshots
evaluables. La auditoría agregada reconcilia los tres buckets contra el mismo
denominador por scope:

- **Todos los equipos con al menos un reporte directo:** 359,088 grupos y
  1,669,554 employee-snapshots. Con `manager_at_exit`, el bucket `2+` es
  0.1546% de grupos y 0.3813% de employee-snapshots; con la sensibilidad es
  0.1551% y 0.3820%.
- **Equipos con más de cinco reportes directos:** 102,055 grupos y 857,897
  employee-snapshots. Con `manager_at_exit`, el bucket `2+` es 0.3733% de
  grupos y 0.6721% de employee-snapshots; con la sensibilidad es 0.3753% y
  0.6735%.

La regla pasa para el cálculo agregado. Se observaron 1,671 eventos
voluntarios; 1,588 tienen manager atribuible y 83 quedan sin atribución. La
auditoría también encontró 298 referencias de manager no resueltas en el
directorio activo y 38,254 empleados con más de un manager histórico en la
ventana; estas condiciones se reportan, pero no se imputan ni se muestran a
nivel individual.

**SQL ejecutado:** `queries/audits/more_than_1_employee_leaves_team_6m_20260908.sql`.
**Evidencia congelada:**
`output/distribution/json/attrition-43-variable-distributions-v2.more-than-1-employee-leaves-evidence-20260908.json`.

## Revalidación de publicación: serie mensual por empleados — 2026-09-08

La visual principal ya no publica el porcentaje acumulado de `team-snapshot
groups`. La métrica mensual se calcula de forma independiente para cada
snapshot evaluable y cada scope:

```text
empleados cuyo equipo tuvo 2+ salidas Voluntary en (t - 6 meses, t]
/ empleados distintos con equipo directo observable en t
```

La consulta devuelve 40 puntos por cada scope y atribución (160 puntos en
total). Los dos scopes son `all_teams` (al menos un reporte directo) y
`teams_gt_5` (al menos seis reportes directos). Las atribuciones son
`manager_at_evaluation` —manager disponible al evaluar `t`— y
`manager_at_exit` —último manager no nulo observado hasta `term_date`—.

La auditoría ejecutada confirma 40 snapshots evaluables, seis snapshots por
ventana y cero puntos con numerador mayor que el denominador. Cada porcentaje
reconcilia con `flagged_employees / observable_employees * 100`, usando
`COUNT(DISTINCT employee_id)`. Los buckets agregados `0`, `1` y `2+` se
conservan sólo como evidencia secundaria de auditoría; no se muestran como
la visual principal.

**SQL ejecutado:** `queries/audits/more_than_1_employee_leaves_team_6m_20260908.sql`.
**Evidencia congelada:**
`output/distribution/json/attrition-43-variable-distributions-v2.more-than-1-employee-leaves-evidence-20260908.json`.

### Relaciones con el portafolio

- More than 1 employee leaves in a year depende de Team turnover.
- Comparten employee_id (shared_source_column).
- Comparten is_termed (shared_source_column).
- Comparten manager_employee_id (shared_source_column).
- Comparten term_date (shared_source_column).
- Comparten term_type (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten flag_event (shared_semantic_cue).
- Comparten manager_team_layers (shared_semantic_cue).

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

- `queries\profiles\attrition-43-monthly-fiscal-20260816_06_more-than-1-employee-leaves-in-a-year_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_06_more-than-1-employee-leaves-in-a-year_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_06_more-than-1-employee-leaves-in-a-year_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_06_more-than-1-employee-leaves-in-a-year_is-termed_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_06_more-than-1-employee-leaves-in-a-year_term-type_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:more-than-1-employee-leaves-in-a-year -->

## Revalidación de comparación anual — 2026-09-09

La ventana de seis meses se mantiene como la definición primaria de la
feature. Se añadió una sensibilidad descriptiva de doce meses únicamente para
comparar la magnitud de la exposición; no sustituye la feature seleccionada ni
se interpreta como ranking de managers o evidencia causal.

- **Ventanas:** primaria `(snapshot - 6 meses, snapshot]`; comparación anual
  `(snapshot - 12 meses, snapshot]`.
- **Población y grano:** empleados regulares activos con equipo directo
  observable, por `scope × attribution × employee snapshot` mensual. Ambas
  ventanas usan salidas con `term_type = 'Voluntary'` y el mismo denominador.
- **Cobertura anual:** 36 de los 40 cortes semestrales tienen historia anual
  completa, desde 2021-06-27 hasta 2026-08-23. Los cuatro cortes iniciales
  (2020-12-27, 2021-03-28, 2021-04-25 y 2021-05-23) se omiten sólo del panel
  anual por no contar con el año previo completo.
- **Regla previa de completitud:** al menos 12 snapshots mensuales distintos y
  al menos 330 días observados en la ventana anual. Una ventana completa puede
  contener 12 o 13 cierres mensuales; no se exigieron exactamente 12.
- **Resultado de aceptación:** 144 puntos publicados (36 fechas × 2 scopes ×
  2 atribuciones), sin denominadores menores de 30, duplicados de membresía,
  numeradores superiores al denominador, discrepancias de denominador frente a
  seis meses ni conteos anuales menores que el conteo semestral anidado.

**Artefactos trazables:**

- Plan: `config/more_than_1_employee_leaves_annual_distribution_plan_v4_20260909.yaml`.
- SQL anual: `queries/audits/more_than_1_employee_leaves_team_12m_20260909.sql`.
- Cobertura: `queries/audits/more_than_1_employee_leaves_annual_window_coverage_20260909.sql`.
- Evidencia congelada: `output/distribution/json/more-than-1-employee-leaves-annual-evidence-20260909.json`.

La visualización de los slides 9–10 coloca los seis meses arriba y los doce
meses abajo, con la misma escala vertical dentro de cada scope para facilitar
la comparación directa.

## Cohorte descriptiva posterior a una salida inicial — 2026-09-11

Esta revisión responde a una pregunta distinta de la bandera histórica de
`2+` salidas: **después de una salida Voluntary inicial, ¿el equipo restante
muestra más attrition Voluntary durante los seis cierres siguientes?** El
artefacto se clasifica como `presentation`: sólo contiene agregados, no expone
integrantes, managers, identificadores ni estratos internos y cada punto
publicado conserva `n >= 30`.

- **Cohorte y población:** `Employee` + `Regular` activos con manager
  observable al índice `2026-03-29`; seguimiento hasta `2026-09-27`.
- **Exposición:** una única salida `Voluntary` reconciliada en los seis
  intervalos cerrados previos, ocurrida en el último intervalo antes del
  cierre índice. La intersección se exige en
  `post_hire_monthly_worker_dtls` y `all_terminations` por empleado, fecha y
  tipo de terminación; los IDs sólo se usan dentro del join.
- **Referencia:** equipos sin salida `Voluntary` reciente, en el mismo cierre
  y bandas de tamaño `1–5`, `6–10`, `11–20` y `21+`; se estandariza a la
  distribución de tamaños de la cohorte expuesta.
- **Seguimiento y censura:** se sigue al roster índice únicamente mientras
  conserva el manager índice. Se censura en cambio de manager, salida no
  `Voluntary` o pérdida de observación.
- **Métrica:** incidencia acumulada Kaplan–Meier a partir de hazards mensuales
  estandarizados; no es una feature disponible al índice ni se reutiliza para
  predecir a una persona.

### Validación y resultado

La regla de aceptación definida antes de ejecutar exigía 24 puntos (dos
scopes × dos series × seis meses), `n` en riesgo de al menos 30, hazards entre
0 y 100, seis cierres completos, episodios índice positivos y concordancia
Voluntary mensual de al menos 99%. La ejecución pasó: 260 episodios índice,
24 puntos publicados, ningún duplicado de evento en `all_terminations` y
99.7994% de concordancia mensual Voluntary.

- **Todos los equipos:** 1,461 integrantes expuestos frente a 41,617 en la
  referencia ajustada; incidencia acumulada a seis meses de **4.88%** frente
  a **2.88%** (`+2.00 pp` descriptivos).
- **Sensibilidad, equipos de 6+ personas:** 978 integrantes expuestos frente
  a 20,155 en la referencia ajustada; **5.74%** frente a **2.91%** a seis
  meses (`+2.83 pp` descriptivos).

La evidencia muestra una **asociación descriptiva** en una cohorte reciente;
no prueba contagio ni causalidad, no evalúa managers, no crea rankings y no
autoriza predicción individual. Una cohorte puntual tampoco demuestra
estabilidad histórica: debe repetirse cuando exista un nuevo sexto cierre.
Esta comparación no cambia automáticamente la definición histórica, el score
ni la elegibilidad de la variable para el modelo.

**Artefactos trazables:**

- Plan: `config/team_post_exit_attrition_event_study_plan_v5_20260911.yaml`.
- Calendario: `queries/audits/team_post_exit_attrition_calendar_20260911.sql`.
- Reconciliación: `queries/audits/team_post_exit_attrition_event_source_reconciliation_20260910.sql`.
- Cohorte estática: `queries/audits/team_post_exit_attrition_static_snapshot_20260911.sql`.
- SQL materializado: `output/distribution/team-post-exit-attrition-static-cohort-20260911.sql`.
- Evidencia congelada: `output/distribution/json/attrition-43-variable-distributions-v2.team-post-exit-attrition-evidence-20260911.json`.
