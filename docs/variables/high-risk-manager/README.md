# High risk manager

## Metodología propuesta y decisión de diseño (2026-08-21)

### Interpretación acordada

La variable busca identificar managers bajo los cuales ocurre una rotación
voluntaria persistentemente mayor que la esperada. La hipótesis es que la
experiencia de liderazgo puede contribuir al attrition de las personas a su
cargo.

Esta señal representa una asociación histórica ajustada, no una demostración
causal ni una evaluación automática del desempeño del manager. Su uso previsto
es analítico y agregado; no debe utilizarse por sí sola para tomar acciones
individuales sobre un manager.

### Definición propuesta

En cada snapshot mensual, un manager se considera de alto riesgo cuando la
rotación voluntaria observada entre sus reportes directos durante los 12 meses
cerrados anteriores es materialmente mayor que la rotación esperada para una
población comparable, después de ajustar equipos pequeños y exigir persistencia
temporal.

La salida principal debe ser un score continuo a nivel `manager-snapshot`. El
flag `high_risk_manager` será una categorización secundaria. Para usarlo como
feature de attrition, cada empleado-snapshot recibe el score de su manager
vigente en ese mismo cierre mensual.

### Cálculo propuesto

1. Reconstruir mensualmente la membresía del equipo mediante
   `manager_employee_id`, conservando una sola relación empleado-manager por
   snapshot.
2. Atribuir cada salida voluntaria al último manager observado en un snapshot
   cerrado anterior a `term_date`. No atribuir el evento al manager sustituto ni
   utilizar información posterior al snapshot de predicción.
3. Para cada manager y snapshot, usar una ventana retrospectiva de 12 meses
   cerrados y calcular:
   - salidas voluntarias observadas del equipo;
   - empleado-meses de exposición;
   - número de reportes distintos;
   - salidas esperadas para esos mismos empleado-meses.
4. Estimar las salidas esperadas con un baseline que excluya el identificador y
   las features del manager. El baseline debe controlar, como mínimo, mes,
   región, job family, nivel y tenure, para no penalizar a managers que reciben
   equipos con un riesgo estructuralmente mayor.
5. Calcular el exceso de attrition:

   `ratio_exceso = salidas_voluntarias_observadas / salidas_voluntarias_esperadas`

6. Aplicar shrinkage o un modelo jerárquico para acercar el ratio a 1 cuando el
   equipo tenga poca exposición. Así, una sola salida no convierte
   automáticamente a un manager con equipo pequeño en alto riesgo.
7. Convertir el resultado ajustado a un percentil mensual entre managers
   elegibles. Este percentil será el `manager_risk_score` continuo.

### Regla inicial para el flag

Como punto de partida, `high_risk_manager = 1` cuando se cumplan todas estas
condiciones:

- `ratio_exceso` ajustado mayor o igual a 1.5;
- manager ubicado en el 10% superior del `manager_risk_score`;
- condición presente en al menos 3 de los últimos 6 snapshots;
- al menos 5 reportes distintos y 60 empleado-meses de exposición.

Cuando no exista historia suficiente, el resultado será `Unknown`, no cero. Los
valores 12 meses, 1.5, 10%, 3 de 6, 5 reportes y 60 empleado-meses son parámetros
iniciales: deben calibrarse mediante evaluación out-of-time antes de aprobar la
versión productiva.

### Reglas temporales y casos especiales

- Usar únicamente terminaciones conocidas al cierre del snapshot.
- Contar inicialmente sólo attrition voluntario; salidas involuntarias, layoffs
  y eventos organizacionales masivos deben excluirse o ajustarse explícitamente.
- Resolver cambios de manager con la relación histórica vigente antes de cada
  salida.
- Un manager nuevo o sin exposición suficiente permanece como `Unknown`.
- No usar el attrition futuro del empleado evaluado ni información de la ventana
  del outcome.
- Mantener IDs dentro del cálculo y publicar únicamente métricas agregadas.

### Validaciones requeridas antes de producción

- Reconciliar elegibles, matched, unmatched, duplicados y multi-match en el join
  empleado-manager-fecha.
- Comparar dos implementaciones independientes del cálculo y exigir coincidencia
  dentro de una tolerancia aprobada.
- Evaluar estabilidad por tamaño de equipo, organización y periodo.
- Ejecutar un backtest out-of-time para calibrar ventana, shrinkage y umbrales.
- Revisar eventos de cambio de manager para comprobar si el riesgo del equipo
  cambia después del movimiento; esta prueba aporta contexto causal, pero no lo
  demuestra por sí sola.
- Completar revisión de gobernanza, privacidad y fairness antes de cualquier uso
  individual.

### Relación con otras variables

`Team turnover` es el componente base de rotación. `High turnover under this
person` identifica una tasa histórica elevada mediante un umbral. `High risk
manager` añade ajuste por composición del equipo, shrinkage y persistencia para
estimar una señal más estable asociada al manager.

> Esta metodología es una decisión conceptual y contexto para el próximo
> assessment. No modifica los scores ni convierte el output histórico en
> evidencia vigente; la implementación y sus reglas deben validarse con SQL
> agregado v4 antes de elevar cualquier score.

<!-- BEGIN evaluate-attrition-variable:high-risk-manager -->
## Conocimiento acumulado: High risk manager

_Actualizado por el assessment v4 `high-risk-manager-score-coverage-revalidation-20260821` el 2026-08-21T13:49:29-06:00._

### Contexto del problema

- **Problema:** Reevaluar High risk manager con la metodologia acordada y con todos los insumos necesarios para distinguir managers cuya rotacion voluntaria historica es persistentemente superior a la esperada.
- **Decisión / caso de uso:** Determinar si la variable tiene fuente, cobertura, historia, consistencia y joins suficientes para incorporarse al modelo de attrition, sin confundir disponibilidad de insumos con una formula estadistica ya calibrada.
- **Outcome:** Attrition voluntario del empleado ocurrido despues del snapshot mensual de prediccion y antes del siguiente snapshot.
- **Población:** Empleados regulares activos en cada snapshot mensual de prediccion.
- **Límite de conocimiento:** En cada snapshot solo se usan membresias, atributos y terminaciones conocidos al cierre. Las salidas se atribuyen al ultimo manager observado antes de term_date y nunca se usa attrition futuro.
- **Rol de la variable:** Manager risk
- **Relevancia:** Una rotacion voluntaria persistentemente superior a la esperada bajo un manager puede asociarse con mayor riesgo de salida de sus reportes.

### Definición y fuente evaluadas

- **Definición vigente:** Riesgo historico ajustado de attrition voluntario asociado al manager.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** employee_id, manager_employee_id, fis_mo_end_dt, fiscal_year, worker_type, employee_type, active_status, region, job_family, job_family_group, job_level_primary_position, level_grouped, max_hire_rehire_date, service_date, original_hire_date, is_termed, term_date, term_type
- **Grain:** Manager-snapshot; asignada al empleado-snapshot mensual

### Relaciones con el portafolio

- No se documentaron relaciones contextuales adicionales.

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=2, Effort=0
- **Coverage reciente:** 99.998%.
- **Historia utilizable:** 61.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- Coverage reciente cumplió el threshold del score. Resultado de la prueba: Cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Cumple.
- La prueba aporta contexto para interpretar el concepto, pero no es un requisito definitorio y no puede elevar el score.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- No se requiere acción inmediata; repetir la validación si cambia la fuente o definición.
- No se requiere acción inmediata.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\high-risk-manager-score-coverage-revalidation-20260821_01_high-risk-manager_coverage.sql`
- `queries/audits/high_risk_manager_source_access_20260821.sql`
- `queries/audits/high_risk_manager_consistency_v2_20260821.sql`
- `queries/audits/high_risk_manager_temporal_join_20260821.sql`
- `queries/audits/high_risk_manager_input_components_v2_20260821.sql`
- `queries/audits/high_risk_manager_join_exclusions_v2_20260821.sql`
- `queries/audits/high_risk_manager_score_calculability_v3_20260821.sql`
- `queries/audits/high_risk_manager_coverage_breakdown_v2_20260821.sql`
- `queries/profiles/high_risk_manager_score_coverage_v2_20260821.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 6.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:high-risk-manager -->

<!-- BEGIN evaluate-attrition-variable-run:high-risk-manager:high-risk-manager-revalidation-20260821-4 -->

### Historial de decisión — run `high-risk-manager-revalidation-20260821-4`

_Registrado el 2026-08-21T12:26:31-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (6 puntos).

**Evolución del plan**

- Plan v5: La ejecucion v4 completo las consultas, pero el validador de narrativa marco cuatro frases tecnicas como idioma no espanol. Esta revision solo vuelve explicitas esas frases en espanol y no cambia SQL, poblacion, reglas ni metricas.

**Validaciones y efecto observado**

- **source:** ¿Existen ambas fuentes y todos los campos requeridos por la ruta v3? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **coverage:** ¿Que tan completos estan los controles detallados y el tenure time-safe en cada snapshot? — resultado No cumple; impacto: Coverage quedó en 0 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿La ruta normalizada elimina fechas futuras, duplicados, contradicciones y tipos no clasificados? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Cada salida elegible encuentra un solo manager previo y cada empleado-snapshot un solo manager-score? — resultado Cumple; impacto: Join quedó en 2 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Por que 4,540 eventos voluntarios no tenian snapshot activo-regular reciente? — resultado Cumple; impacto: Join quedó en 2 de acuerdo con la evidencia y los límites v4.
- **coverage:** ¿Que regla explica cada empleado-snapshot no observable en los tres cierres recientes? — resultado Cumple; impacto: Coverage quedó en 0 de acuerdo con la evidencia y los límites v4.
- **history:** ¿Desde cuando y para que proporcion de empleados puede calcularse la feature con historia suficiente? — resultado No cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿La disponibilidad y los joins confirman ya la formula estadistica y sus umbrales? — resultado Informativa; impacto: Evidencia contextual para Definition; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\high-risk-manager-revalidation-20260821-4_01_high-risk-manager_coverage.sql`
- `queries/audits/high_risk_manager_source_access_20260821.sql`
- `queries/audits/high_risk_manager_consistency_v2_20260821.sql`
- `queries/audits/high_risk_manager_temporal_join_20260821.sql`
- `queries/audits/high_risk_manager_input_components_v2_20260821.sql`
- `queries/audits/high_risk_manager_join_exclusions_v2_20260821.sql`
- `queries/audits/high_risk_manager_coverage_breakdown_v2_20260821.sql`
- `queries/profiles/high_risk_manager_feature_coverage_20260821.sql`

<!-- END evaluate-attrition-variable-run:high-risk-manager:high-risk-manager-revalidation-20260821-4 -->

<!-- BEGIN evaluate-attrition-variable-run:high-risk-manager:high-risk-manager-score-coverage-revalidation-20260821 -->

### Historial de decisión — run `high-risk-manager-score-coverage-revalidation-20260821`

_Registrado el 2026-08-21T13:49:29-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (12 puntos).

**Evolución del plan**

- Plan v6: El usuario aclaro que Coverage corresponde al manager_risk_score continuo y que los minimos de equipo e historia solo controlan la confiabilidad o el flag secundario. Esta revision valida cobertura por dependencias obligatorias y calculabilidad con shrinkage, sin cambiar el skill.

**Validaciones y efecto observado**

- **source:** ¿Existen ambas fuentes y todos los campos requeridos por la ruta v3? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **coverage:** ¿Que tan completos estan los controles detallados y el tenure time-safe en cada snapshot? — resultado Cumple; impacto: Coverage quedó en 2 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿La ruta normalizada elimina fechas futuras, duplicados, contradicciones y tipos no clasificados? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Cada salida elegible encuentra un solo manager previo y cada empleado-snapshot un solo manager-score? — resultado Cumple; impacto: Join quedó en 2 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Por que 4,540 eventos voluntarios no tenian snapshot activo-regular reciente? — resultado Cumple; impacto: Join quedó en 2 de acuerdo con la evidencia y los límites v4.
- **coverage:** ¿Cada empleado con insumos completos puede recibir un score continuo de su manager? — resultado Cumple; impacto: Coverage quedó en 2 de acuerdo con la evidencia y los límites v4.
- **coverage:** ¿Cuántos empleados cumplen además los mínimos para un flag de alta confianza? — resultado Cumple; impacto: Evidencia contextual para Coverage; sin capacidad de aumentar el score.
- **history:** ¿Desde cuándo puede calcularse el score continuo con todas sus dependencias obligatorias? — resultado Cumple; impacto: History quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿La disponibilidad y los joins confirman ya la formula estadistica y sus umbrales? — resultado Informativa; impacto: Evidencia contextual para Definition; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\high-risk-manager-score-coverage-revalidation-20260821_01_high-risk-manager_coverage.sql`
- `queries/audits/high_risk_manager_source_access_20260821.sql`
- `queries/audits/high_risk_manager_consistency_v2_20260821.sql`
- `queries/audits/high_risk_manager_temporal_join_20260821.sql`
- `queries/audits/high_risk_manager_input_components_v2_20260821.sql`
- `queries/audits/high_risk_manager_join_exclusions_v2_20260821.sql`
- `queries/audits/high_risk_manager_score_calculability_v3_20260821.sql`
- `queries/audits/high_risk_manager_coverage_breakdown_v2_20260821.sql`
- `queries/profiles/high_risk_manager_score_coverage_v2_20260821.sql`

<!-- END evaluate-attrition-variable-run:high-risk-manager:high-risk-manager-score-coverage-revalidation-20260821 -->
