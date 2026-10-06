# Talent index

<!-- BEGIN evaluate-attrition-variable:talent-index -->
## Conocimiento acumulado: Talent index

_Actualizado por el assessment v4 `talent-index-current-state-final4-20260820` el 2026-08-20T16:23:57-06:00._

### Contexto del problema

- **Problema:** Revalidar Talent index como dato disponible en el estado actual, sin interpretar last_modified_date, airflow_execution_date ni otros timestamps técnicos como fecha de evaluación, publicación o vigencia del índice.
- **Decisión / caso de uso:** Determinar la disponibilidad actual del valor almacenado y qué tan preparada está la fuente para una futura integración de attrition, separando esa conclusión de cualquier afirmación histórica o time-safe.
- **Outcome:** Attrition voluntario posterior al snapshot de predicción; esta revisión no afirma todavía que Talent index pueda reconstruirse históricamente antes del outcome.
- **Población:** Empleados regulares activos en el último snapshot mensual disponible de la tabla laboral.
- **Límite de conocimiento:** Se evalúa lo que hoy puede recuperarse de la fuente. Los timestamps técnicos de carga se excluyen de la semántica y no se usan para inferir cuándo fue evaluado el empleado ni cuándo estuvo disponible el índice.
- **Rol de la variable:** Talent
- **Relevancia:** El índice puede aportar una señal útil, pero su valor longitudinal depende de fórmula, elegibilidad y fechas oficiales aún no demostradas.

### Definición y fuente evaluadas

- **Definición vigente:** Métrica precalculada por empleado-ciclo evaluada únicamente como disponibilidad actual.
- **Tipo semántico:** precomputed_metric
- **Tabla / fuente:** hrda.master_talent_index
- **Columnas:** empl_id, talent_index, cycle_number, cycle_name, perf, stock, bonus, promo_index, talent_quartile, ar_eligibility
- **Grain:** Empleado en el último snapshot laboral; fuente empleado-ciclo

### Relaciones con el portafolio

- No se documentaron relaciones contextuales adicionales.

### Resultado y evidencia agregada

- **Resultado:** Baja - exploratoria (8 puntos).
- **Scores:** Source=2, Definition=1, Coverage=1, Missingness=1, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** 79.2499%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta obtener lineage autoritativo y una reconciliación independiente de fórmula, componentes y tolerancia. Resultado de la prueba: Cumple.
- El coverage observable reciente está por debajo del umbral de 95% para score 2. Resultado de la prueba: Cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Cumple.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta obtener lineage autoritativo y una reconciliación independiente de fórmula, componentes y tolerancia.
- El coverage observable reciente está por debajo del umbral de 95% para score 2.
- Missingness reciente supera el máximo de 5% para score 2.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.

**Acciones recomendadas**

- No se requiere acción inmediata; repetir la validación si cambia la fuente o definición.
- Aprobar la definición y obtener lineage autoritativo y una reconciliación independiente de fórmula, componentes y tolerancia; guardar SQL agregado, regla previa y métricas de reconciliación.
- Resolver brechas de elegibilidad u observabilidad y repetir el perfil; objetivo >= 95%.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.

**SQL y evidencia trazable**

- `queries\profiles\talent-index-current-state-final4-20260820_01_talent-index_coverage.sql`
- `queries/audits/talent_index_current_source_access_audit.sql`
- `queries/audits/talent_index_definition_readiness_audit.sql`
- `queries/profiles/talent_index_current_state_coverage.sql`
- `queries/audits/talent_index_current_structural_consistency_audit.sql`
- `queries/audits/talent_index_current_join_reconciliation_audit.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 5.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:talent-index -->

## Reconciliacion exploratoria de formula — 2026-08-26

### Pregunta y poblacion

Se probaron hipotesis sobre el calculo de `talent_index` contra el valor almacenado en `hrda.master_talent_index`. La poblacion fue el grain interno empleado-ciclo; el perfil encontro 9 ciclos, sin grupos duplicados empleado-ciclo y con al menos 30 observaciones por ciclo. Los ratings `perf`, `stock` y `bonus` toman valores observados 1-5; `promo_index` y `talent_index` estan en una escala observada 0-100.

La comparacion uso solo filas con target y componentes requeridos poblados, y una tolerancia de 0.01 puntos. Los resultados son agregados; no se guardaron IDs ni filas de empleados.

### Versiones probadas

| Hipotesis | Comparable | Match <= 0.01 | Match rate | Error absoluto medio | Conclusion |
| --- | ---: | ---: | ---: | ---: | --- |
| `promo_index` directo | 266,467 | 292 | 0.1096% | 11.2659 | No reproduce el target. |
| Promedio `perf/stock/bonus` normalizado 20-100 | 312,330 | 9 | 0.0029% | 24.1569 | La escala directa no coincide. |
| 25% ratings normalizados + 75% `promo_index` | 265,247 | 360 | 0.1357% | 9.9158 | Mejor suma ponderada fija, pero insuficiente. |
| Variante equivalente con `promo_quartile` | 265,247 | 581 | 0.2190% | 11.6650 | No mejora el error. |
| Ranking lexicografico `stock`, `perf`, `bonus`, `promo_index` con `CUME_DIST` | 265,247 | — | 0.0573% | 6.7917 | Mejor ranking explorado, pero no reproduce valores. |
| Ajuste lineal de `core_ratings_norm20` y `promo_index` entrenado en ciclos 1-6, probado en 7-9 | 102,714 | — | 0.0058% | 7.0080 | La relacion no es una formula estable exacta. |

La cuadrícula de pesos entre ratings y `promo_index` tampoco encontro un peso estable: en escala directa el mejor peso estuvo alrededor de 20-25% de ratings, mientras que en ranking cambio hacia 85-95% de ratings. Cambiar el denominador del ranking para incluir todas las filas con componentes disponibles no altero la conclusion.

### Evidencia adicional

- `talent_index` tiene relaciones fuertes con `stock` y con el promedio de ratings, pero la coincidencia numerica es baja; correlacion no equivale a formula.
- Dentro de `talent_quartile`, la relacion con `promo_index` cambia por ciclo y banda, por lo que no hay una transformacion simple y estable visible.
- El dominio de `talent_quartile` cambia: los ciclos 1-8 muestran 1-4 y el ciclo 9 muestra tambien 5. Este campo se trato como contextual y no se uso para confirmar `talent_index` porque esta relacionado con el target.
- El mejor MAE de los ajustes calibrados fue obtenido por parametros estimados con los mismos datos; eso es un limite estadistico, no lineage de negocio.

### Conclusion y efecto en la evaluacion

No se encontro una formula visible que reproduzca `talent_index` con coincidencia alta y estable entre ciclos. La evidencia reduce la hipotesis de una suma, promedio, ranking simple o reescala fija de los componentes disponibles, pero no identifica el componente oculto ni la regla de negocio. `Definition` permanece en 1 y no debe elevarse a 2 con esta evidencia.

Para confirmar la definicion se necesita el SQL/ETL oficial, un catalogo del owner o una reconciliacion del owner sobre la misma poblacion, incluyendo ordenamiento, poblacion elegible, manejo de empates, fechas, nulls y redondeo.

### Consultas ejecutadas

- `queries/audits/talent_index_formula_candidate_profile_20260826.sql`
- `queries/audits/talent_index_formula_reconciliation_20260826.sql`
- `queries/audits/talent_index_target_relationship_diagnostic_20260826.sql`
- `queries/audits/talent_index_rank_formula_reconciliation_20260826.sql`
- `queries/audits/talent_index_weight_grid_reconciliation_20260826.sql`
- `queries/audits/talent_index_within_quartile_diagnostic_20260826.sql`
- `queries/audits/talent_index_affine_calibration_diagnostic_20260826.sql`
- `queries/audits/talent_index_lexicographic_rank_reconciliation_20260826.sql`
- `queries/audits/talent_index_rank_population_reconciliation_20260826.sql`
- `queries/audits/talent_index_multivariate_calibration_diagnostic_20260826.sql`

## Formula de los dos ultimos ciclos de AR - 2026-08-26

### Fuente de la hipotesis

La presentacion proporcionada por el usuario, `Talent Index Refresh_6.19.26.pptx`,
describe una formula basada en los dos ultimos ciclos de AR:

- `Stock promedio = (Stock t-1 + Stock t) / 2`
- `Performance promedio = (Performance t-1 + Performance t) / 2`
- `Talent Index = 1,000,000 * Stock promedio + 500 * Performance promedio`

Esta fuente documenta una regla propuesta o comunicada, pero no constituye por
si sola lineage del campo `hrda.master_talent_index.talent_index`.

### Diseno de la validacion

Se comparo el target almacenado en el ciclo actual `t` contra la formula usando
los ratings del mismo empleado en `t-1` y `t`. Se probaron todos los pares
consecutivos disponibles y se reviso por separado el ultimo par disponible,
`8 -> 9`. La poblacion comparable exigio un registro unico por empleado-ciclo,
ratings `stock` y `perf` presentes en ambos ciclos y `talent_index` presente en
el ciclo actual. La tolerancia fue `0.01` puntos y cada ciclo reportado tuvo al
menos 30 casos.

Los tipos de fuente quedaron confirmados mediante metadata:

- `empl_id`: `integer`
- `cycle_number`: `integer`
- `stock`: `integer`
- `perf`: `integer`
- `talent_index`: `numeric(15,4)`

Por tanto, los promedios pueden tomar valores con medio punto aunque los
ratings almacenados sean enteros.

### Resultado del ultimo par `8 -> 9`

La calidad de la poblacion no explica el desacuerdo: hubo 42,789 empleados
presentes en ambos ciclos, cero grupos duplicados, cero contradicciones y
37,636 filas comparables. Los faltantes redujeron la poblacion, pero no se
detectaron duplicados ni conflictos de valores.

| Candidato | Match <= 0.01 | Match rate | Error absoluto medio |
| --- | ---: | ---: | ---: |
| Formula bruta con promedio de dos ciclos | 0 | 0.0000% | 3,791,545.0005 |
| Formula de dos ciclos reescalada a 0-100 | 0 | 0.0000% | 19.1684 |
| Ranking `CUME_DIST` con promedio de dos ciclos | 4 | 0.0106% | 16.2971 |
| `PERCENT_RANK` con promedio de dos ciclos | 25 | 0.0664% | 17.6837 |
| Baseline: `CUME_DIST` del ciclo actual | 57 | 0.1515% | 8.1333 |
| Baseline: ciclo actual reescalado a 0-100 | 48 | 0.1275% | 17.6074 |

La formula bruta produce valores entre aproximadamente `1,000,500` y
`5,002,500`, mientras que el campo almacenado observado esta entre `0` y
`100`. Las transformaciones de escala y ranking tampoco reproducen el target;
ademas, el promedio de dos ciclos empeora frente a usar solo el ciclo actual.

En todos los pares consecutivos, la version de dos ciclos obtuvo `0.0000%` de
match en bruto, `0.0155%` con min-max, `0.0188%` con `CUME_DIST` y `0.0475%`
con `PERCENT_RANK`. Ninguna se acerca a la regla de aceptacion del 95%.

### Conclusion

La formula de la PPT no reproduce el `talent_index` almacenado, ni como valor
bruto, ni despues de una reescala teorica, ni como ranking simple. Esto no
descarta que sea una formula propuesta para un refresh futuro; solo demuestra
que no es una reconstruccion del campo actual con los componentes y la
poblacion probados. Podria faltar una normalizacion, una poblacion elegible,
un desempate o un componente adicional que no esta visible en esta tabla.

`Definition` permanece en 1. No se eleva a 2 porque falta lineage oficial y la
reconciliacion independiente no pasa la regla de aceptacion.

### Consultas de esta validacion

- `queries/audits/talent_index_last_two_cycles_average_formula_reconciliation_20260826.sql`
- `queries/audits/talent_index_last_two_cycles_latest_pair_quality_20260826.sql`
- `queries/audits/talent_index_formula_source_schema_audit_20260826.sql`
- `queries/audits/talent_index_source_access_audit.sql`

<!-- BEGIN evaluate-attrition-variable-run:talent-index:talent-index-revalidation-final6-20260820 -->

### Historial de decisión — run `talent-index-revalidation-final6-20260820`

_Registrado el 2026-08-20T13:43:05-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (8 puntos).

**Evolución del plan**

- Plan v4: El plan v2 incorporo el follow-up del dominio de talent_quartile. El intento v3 corrigio la redaccion del join, pero introdujo una codificacion incorrecta del signo inicial de interrogacion. El plan v4 conserva SQL, metricas y umbrales, aclara la regla del join y restaura preguntas validas en espanol.

**Validaciones y efecto observado**

- **source:** ¿Existen y son accesibles la tabla y todas las columnas necesarias? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Hay filas comparables para reconciliar el indice cuando se obtenga la formula oficial? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **coverage:** ¿Que porcentaje de empleados-snapshot activos tiene un Talent index conocido a tiempo? — resultado Cumple; impacto: Coverage quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿La llave empleado-ciclo-version es unica y el valor almacenado carece de conflictos? — resultado No cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Los valores de talent_quartile fuera de 1 a 4 son un sentinel documentado u otro dominio? — resultado No cumple; impacto: Evidencia contextual para Consistency; sin capacidad de aumentar el score.
- **consistency:** ¿Cada ciclo tiene una fecha de conocimiento unica y util para el modelado historico? — resultado No cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El join produce exactamente un Talent index por empleado-snapshot elegible? — resultado No cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿La profundidad historica representa valores realmente conocidos a tiempo? — resultado No cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.
- **effort:** ¿La feature es SQL directo o requiere reglas y transformacion moderadas? — resultado No cumple; impacto: Effort quedó en 1 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿La tabla contiene enriquecimiento posterior a la salida aunque eso no pruebe la formula? — resultado Informativa; impacto: Evidencia contextual para Definition; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\talent-index-revalidation-final6-20260820_01_talent-index_coverage.sql`
- `queries/audits/talent_index_source_access_audit.sql`
- `queries/audits/talent_index_definition_readiness_audit.sql`
- `queries/profiles/talent_index_target_population_coverage.sql`
- `queries/audits/talent_index_structural_consistency_audit.sql`
- `queries/audits/talent_index_quartile_domain_audit.sql`
- `queries/audits/talent_index_cycle_timing_summary_audit.sql`
- `queries/audits/talent_index_join_reconciliation_audit.sql`
- `queries/audits/talent_index_post_outcome_context_audit.sql`

<!-- END evaluate-attrition-variable-run:talent-index:talent-index-revalidation-final6-20260820 -->

<!-- BEGIN evaluate-attrition-variable-run:talent-index:talent-index-current-state-final4-20260820 -->

### Historial de decisión — run `talent-index-current-state-final4-20260820`

_Registrado el 2026-08-20T16:23:57-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (8 puntos).

**Evolución del plan**

- Plan v5: El usuario aclaró que last_modified_date y airflow_execution_date indican carga o procesamiento técnico y pueden cambiar cuando se sobrescriben tablas completas. Este plan retira esos campos de Coverage, History, Join y de cualquier inferencia post-outcome, y limita la evaluación a disponibilidad actual.

**Validaciones y efecto observado**

- **source:** ¿Existen y son accesibles la tabla y las columnas necesarias para la evaluación actual? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Hay valor almacenado y componentes candidatos para una futura reconciliación de fórmula? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **coverage:** ¿Qué porcentaje de empleados activos tiene actualmente un Talent index recuperable? — resultado Cumple; impacto: Coverage quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿La llave empleado-ciclo es única y carece de conflictos o mappings contradictorios? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El join actual produce como máximo un registro seleccionado por empleado elegible? — resultado No cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Cuánto cambia la observabilidad si se exige el mayor ciclo global en vez del mayor ciclo de cada empleado? — resultado Informativa; impacto: Evidencia contextual para Join; sin capacidad de aumentar el score.
- **history:** ¿Esta revisión demuestra historia utilizable del Talent index? — resultado Cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.
- **effort:** ¿La recuperación actual es directa o requiere transformación y reglas adicionales? — resultado Cumple; impacto: Effort quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\talent-index-current-state-final4-20260820_01_talent-index_coverage.sql`
- `queries/audits/talent_index_current_source_access_audit.sql`
- `queries/audits/talent_index_definition_readiness_audit.sql`
- `queries/profiles/talent_index_current_state_coverage.sql`
- `queries/audits/talent_index_current_structural_consistency_audit.sql`
- `queries/audits/talent_index_current_join_reconciliation_audit.sql`

<!-- END evaluate-attrition-variable-run:talent-index:talent-index-current-state-final4-20260820 -->

## Reconciliacion de la hipotesis de Mandy - 2026-08-27

### Pregunta y poblacion

Se evaluo si la explicacion de Mandy reproduce el `talent_index` almacenado:
usar los ratings mas recientes de `stock` y `perf`, convertirlos a percentiles
dentro de un grupo tipo `comp grade`, ponderar `stock` con `1,000,000` y
`perf` con `500`, y convertir el resultado a un ranking final.

La tabla `hrda.master_talent_index` no tiene una columna llamada
`compensation_grade`. Por eso se probaron `rewards_group` y `level` solo como
candidatos tecnicos. La poblacion comparable fue el grain empleado-ciclo con
`stock`, `perf`, `talent_index` y el grupo poblados, sin contradicciones dentro
del empleado-ciclo. Se observaron los ciclos 1 a 9 y 313,524 observaciones
comparables usando todos los grupos. Al exigir grupos de al menos 30 personas,
quedaron 313,038 observaciones para `rewards_group` y 313,467 para `level`.

### Metodo y regla de aceptacion

Se calcularon `PERCENT_RANK` y `CUME_DIST` para `stock` y `perf` dentro de cada
candidato de grupo y ciclo. Se probaron el valor ponderado directo, el ranking
final dentro del ciclo y el ranking final dentro del grupo. La tolerancia fue
`0.01`; una variante solo se consideraria reconciliada con al menos 95% de
coincidencias en cada ciclo con al menos 30 casos. La consulta fue agregada y
no publico IDs ni etiquetas de grupo.

### Resultado observado

- Mejor variante con `level` y grupos de al menos 30: `final_percent_rank_cycle`,
  match rate de `0.1282%` y MAE de `7.9039`.
- Mejor variante con `rewards_group` y grupos de al menos 30:
  `final_percent_rank_cycle`, match rate de `0.0604%` y MAE de `8.0080`.
- Las variantes del valor ponderado directo tuvieron esencialmente cero
  coincidencias y errores medios de aproximadamente `337,000`, lo que confirma
  que esa expresion no esta en la escala `0-100` del target.
- Ningun ciclo ni ninguna variante paso la regla de aceptacion de 95%.

### Conclusion y siguiente accion

La explicacion de Mandy es una hipotesis razonable sobre el ordenamiento, pero
no reproduce el `talent_index` actual. Tampoco se pudo confirmar que
`rewards_group` o `level` sea el `comp grade` oficial. `Definition` permanece
en 1 y no debe elevarse a 2.

Para cerrar la definicion se necesita la query o ETL oficial de Raj, incluyendo
el mapping de `comp grade`, la regla para grupos pequenos, el manejo de empates,
la poblacion elegible, el ciclo AR usado y la transformacion final a la escala
almacenada.

### Consulta ejecutada

- `queries/audits/talent_index_within_comp_grade_weighted_reconciliation_20260827.sql`
- Ejecucion: 2026-08-27
- Resultado: `outcome: pass` para la ejecucion de la auditoria; la regla de
  reconciliacion no paso.

## Revisión de attrition por cohorte de agosto — 2026-09-22

### Pregunta y regla propuesta

Se revisó si el slide puede mostrar attrition voluntario anual por banda de
`talent_index` siguiendo esta lógica: fijar la banda de cada empleado activo en
el cierre fiscal de agosto y contar las salidas voluntarias de esas mismas
personas durante los doce meses posteriores. La regla es metodológicamente
correcta, siempre que el valor del índice estuviera efectivamente conocido en
el baseline.

La regla de aceptación se fijó antes de ejecutar las consultas: debe existir
una fecha de negocio oficial —de evaluación, vigencia o publicación— que
vincule un ciclo con el snapshot de agosto. La llave empleado-ciclo debe ser
única, sin valores contradictorios. `last_modified_date`,
`airflow_execution_date` y `airflow_db_processing_ts` son timestamps técnicos
y no se tratan como fechas de conocimiento.

### Evidencia agregada

- La metadata de `hrda.master_talent_index` contiene nueve ciclos y sólo tres
  columnas de fecha/timestamp: `last_modified_date`,
  `airflow_execution_date` y `airflow_db_processing_ts`. No hay una fecha de
  negocio que relacione un ciclo con un snapshot de fuerza laboral.
- Los cierres de agosto disponibles para una ventana anual completa son
  2023-08-20, 2024-08-25 y 2025-08-24.
- El join por empleado y ciclo es técnicamente limpio: en los 27 cruces
  baseline-ciclo revisados no hubo empleados con filas duplicadas ni con valores
  de `talent_index` conflictivos.
- La temporalidad no pasa la regla. Los ciclos 1–6 comparten la misma fecha
  técnica (2023-03-09), el ciclo 7 no tiene fecha técnica, el ciclo 8 tiene
  2025-01-06 y el ciclo 9 tiene 2025-11-13. En particular, el ciclo 9 —que
  cubre 40,375 de los 41,757 empleados del baseline 2025 con valor único— fue
  cargado técnicamente después de 2025-08-24; aun así, esa fecha técnica no se
  puede usar para fechar los demás ciclos ni para demostrar su disponibilidad
  de negocio.

### Conclusión y efecto en el slide

La condición de conocimiento no está demostrada. Por ello no se calcula ni se
publica attrition por banda de Talent Index: aplicar retrospectivamente el
último ciclo recuperable al baseline podría incorporar información futura. El
estado **Not estimable** del slide se mantiene y no refleja un fallo del cálculo
de attrition ni falta de tamaño de muestra.

Cuando el owner entregue la fecha oficial de vigencia/publicación de cada ciclo
o una tabla histórica con snapshot, el cálculo será: banda conocida al cierre
de agosto, cohorte fija, salidas estrictamente `term_type='VOLUNTARY'` en
`(baseline, baseline + 12 meses]`, y publicación sólo para bandas con al menos
30 personas en el baseline.

### Consultas ejecutadas

- `queries/audits/talent_index_snapshot_history_schema_audit_20260921.sql`
- `queries/audits/talent_index_cycle_timing_audit.sql`
- `queries/audits/talent_index_cycle_timing_summary_audit.sql`
- `queries/audits/talent_index_august_baseline_time_safety_audit_20260922.sql`
