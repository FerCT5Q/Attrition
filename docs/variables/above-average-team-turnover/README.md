# Above-average team turnover

## Propósito y definición operativa

Esta es la candidata 44: una señal binaria de **contexto histórico del equipo** que un reporte directo actual hereda de su manager vigente. No sustituye ninguna señal previa ni evalúa a una persona manager.

En cada cierre mensual `t`, para empleados regulares activos con `manager_employee_id`:

- `1` indica que el manager es elegible y que su tasa histórica de salidas `Voluntary`, expresada como equivalente a seis meses, es al menos `1.3 ×` el benchmark ponderado de managers elegibles.
- `0` indica que el manager es elegible y queda debajo de ese umbral.
- `Unknown` preserva los casos sin historia o exposición suficiente; nunca se transforma en `0`.

El cálculo usa los 18 intervalos mensuales cerrados anteriores a `t` (19 cierres). Sólo cuentan salidas con `term_type = 'Voluntary'`; se excluyen `Voluntary Exception`, involuntarias y nulos. Cada salida se atribuye al manager del empleado al inicio del intervalo mensual en el que ocurre. Un manager requiere exposición en los 18 intervalos, tamaño promedio de equipo de al menos 4 reportes y al menos 2 salidas voluntarias distintas. El benchmark es `salidas Voluntary / exposición histórica elegible × 6`, equivalente al promedio de tasas de manager ponderado por tamaño medio de equipo.

La asignación se realiza al reporte directo vigente desde su primer snapshot, sin exigir una convivencia mínima empleado-manager. Es una asociación histórica y sensible: no demuestra causalidad, no es una evaluación individual de managers y no es una feature productiva aprobada. El umbral de trabajo `1.3×` se eligió como sensibilidad inicial y debe revisarse con estabilidad temporal, evaluación out-of-time y gobierno antes de cualquier uso operativo.

## Relación con las señales de manager existentes

- `High risk manager` usa un ratio continuo observado/esperado con estratificación y suavizamiento; no es la misma tasa ni el mismo umbral.
- `High turnover under this person` muestra el conteo descriptivo histórico `0 / 1 / 2+` de salidas voluntarias; no compara contra un benchmark de peers.
- `Manager leaving` indica exposición de la persona a la salida voluntaria de su manager previo; es un evento individual distinto del historial del equipo.

La evidencia de presentación está congelada en `output/distribution/json/above-average-team-turnover-evidence-20260911-threshold-1_3.json`, sin IDs, nombres, tasas individuales ni rankings de managers. El cálculo visible proviene de `queries/profiles/above_average_team_turnover_presentation_distribution_20260911_threshold_1_3.sql`; las pruebas de historia, atribución, deduplicación y reconciliación están en `queries/audits/above_average_team_turnover_18m_audit_20260910.sql` y `queries/audits/above_average_team_turnover_termination_reconciliation_20260910.sql`.

La fuente primaria es `hrda.post_hire_monthly_worker_dtls`, alineada con las señales actuales. La discrepancia agregada con `all_terminations` se conserva como límite de definición: hasta contar con lineage o una reconciliación aprobada, `Definition` permanece en 1.

## Sensibilidad del umbral y significancia aproximada

La auditoría agregada `queries/audits/above_average_team_turnover_threshold_sensitivity_20260911.sql` compara `1.2×`, `1.3×` y `1.4×` en seis cierres. En el último cierre, entre 500 managers elegibles, la distribución de la tasa relativa tiene p25 `0.875×`, mediana `1.166×`, p75 `1.526×`, p90 `1.875×` y p95 `2.377×`. Por eso `1.3×` queda por encima de la mediana y conserva una selección superior al promedio sin convertir el umbral en una evaluación individual.

Con el mismo benchmark de `9.709%` equivalente a seis meses, `1.3×` asigna `1,116` flags (`25.1%` de los `4,445` reportes con manager elegible) frente a `902` (`20.3%`) con `1.4×`. La proporción de `1.3×` se mantuvo entre `24.6%` y `26.9%` en los seis cierres; `1.2×` sube a aproximadamente `31%` y es menos selectivo. El cambio no reduce por sí solo los `45,761` `Unknown`: esos casos provienen de historia o exposición insuficiente.

Como control de significancia se calculó un límite inferior unilateral aproximado de 95% para la proporción de salidas por employee-month, convertido a seis meses y comparado con el benchmark. En el último cierre pasan ese screening `145` reportes; el resultado no es una prueba causal, no corrige dependencia entre meses ni la incertidumbre del benchmark y no se usa como corte operativo. `1.3×` se conserva como umbral de trabajo inicial y requiere backtest out-of-time y gobierno.

La evidencia congelada está en `output/distribution/json/above-average-team-turnover-threshold-sensitivity-20260911.json`. Los conteos de managers inferiores a `n=30` se suprimen; no se guardan identidades, tasas individuales ni rankings.

<!-- BEGIN evaluate-attrition-variable:above-average-team-turnover -->
## Conocimiento acumulado: Above-average team turnover

_Actualizado por el assessment v4 `above-average-team-turnover-v4-20260910-r13` el 2026-09-11T07:08:17-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente un portafolio de variables de RH para determinar su utilidad, relación y preparación para el caso de uso configurado.
- **Decisión / caso de uso:** Analizar contexto de retención asociado al equipo, no calificar managers ni tomar decisiones individuales.
- **Outcome:** Por confirmar.
- **Población:** Empleados regulares activos con manager_employee_id al cierre mensual t.
- **Límite de conocimiento:** Cierre mensual t; se excluye toda terminación posterior a t.
- **Rol de la variable:** Manager risk
- **Relevancia:** Añade una señal binaria simple de contexto del equipo, sin sustituir High risk manager ni High turnover under this person.

### Definición y fuente evaluadas

- **Definición vigente:** Señal binaria de contexto del manager basada en rotación voluntaria histórica relativa y asignada al reporte directo actual.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** employee_id, manager_employee_id, fis_mo_end_dt, fiscal_year, worker_type, employee_type, active_status, term_date, term_type
- **Grain:** Empleado-snapshot mensual que hereda una señal manager-snapshot

### Relaciones con el portafolio

- No se documentaron relaciones contextuales adicionales.

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (7 puntos).
- **Scores:** Source=2, Definition=1, Coverage=0, Missingness=0, Consistency=1, History=0, Join=2, Effort=1
- **Coverage reciente:** 9.1755%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Cumple parcialmente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- El coverage observable reciente está por debajo del mínimo de 70% para score 1.
- Missingness reciente supera el máximo de 30% para score 1.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.

**Acciones recomendadas**

- No se requiere acción inmediata; repetir la validación si cambia la fuente o definición.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Resolver brechas de elegibilidad u observabilidad y repetir el perfil; objetivo >= 95%.
- Investigar brechas por fecha y segmento elegible; objetivo <= 5% sin patrón sistemático.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.

**SQL y evidencia trazable**

- `queries\profiles\above-average-team-turnover-v4-20260910-r13_01_above-average-team-turnover_coverage.sql`
- `queries/audits/above_average_team_turnover_source_access_20260910.sql`
- `queries/audits/above_average_team_turnover_18m_audit_20260910.sql`
- `queries/audits/above_average_team_turnover_termination_reconciliation_20260910.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 3.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:above-average-team-turnover -->

<!-- BEGIN evaluate-attrition-variable-run:above-average-team-turnover:above-average-team-turnover-v4-20260910-r12 -->

### Historial de decisión — run `above-average-team-turnover-v4-20260910-r12`

_Registrado el 2026-09-11T07:06:38-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (7 puntos).

**Evolución del plan**

- Plan v3: La auditoría v2 encontró seis diferencias de precisión al comparar el benchmark calculado con tasas de manager ya redondeadas contra su equivalente por exposición. Esta revisión preserva la ponderación por tamaño medio (exposición/18) y calcula el benchmark con su forma algebraicamente exacta: salidas elegibles / exposición elegible * 6. Así evita que el redondeo cambie una comparación en el límite 1.4.

**Validaciones y efecto observado**

- **source:** ¿Existen ambas tablas y todos los campos de la ruta? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Las salidas, la historia de 18 intervalos y el join al reporte actual son únicos y time-safe? — resultado Cumple; impacto: Join quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Se aplican 18, >=4, >=2 y >=1.4, y el benchmark ponderado reconcilia exactamente? — resultado Cumple parcialmente; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Qué diferencias agregadas existen entre la fuente primaria y all_terminations? — resultado Cumple parcialmente; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\above-average-team-turnover-v4-20260910-r12_01_above-average-team-turnover_coverage.sql`
- `queries/audits/above_average_team_turnover_source_access_20260910.sql`
- `queries/audits/above_average_team_turnover_18m_audit_20260910.sql`
- `queries/audits/above_average_team_turnover_termination_reconciliation_20260910.sql`

<!-- END evaluate-attrition-variable-run:above-average-team-turnover:above-average-team-turnover-v4-20260910-r12 -->

<!-- BEGIN evaluate-attrition-variable-run:above-average-team-turnover:above-average-team-turnover-v4-20260910-r13 -->

### Historial de decisión — run `above-average-team-turnover-v4-20260910-r13`

_Registrado el 2026-09-11T07:08:17-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (7 puntos).

**Evolución del plan**

- Plan v3: La auditoría v2 encontró seis diferencias de precisión al comparar el benchmark calculado con tasas de manager ya redondeadas contra su equivalente por exposición. Esta revisión preserva la ponderación por tamaño medio (exposición/18) y calcula el benchmark con su forma algebraicamente exacta: salidas elegibles / exposición elegible * 6. Así evita que el redondeo cambie una comparación en el límite 1.4.

**Validaciones y efecto observado**

- **source:** ¿Existen ambas tablas y todos los campos de la ruta? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Las salidas, la historia de 18 intervalos y el join al reporte actual son únicos y time-safe? — resultado Cumple; impacto: Join quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Se aplican 18, >=4, >=2 y >=1.4, y el benchmark ponderado reconcilia exactamente? — resultado Cumple parcialmente; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Qué diferencias agregadas existen entre la fuente primaria y all_terminations? — resultado Cumple parcialmente; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\above-average-team-turnover-v4-20260910-r13_01_above-average-team-turnover_coverage.sql`
- `queries/audits/above_average_team_turnover_source_access_20260910.sql`
- `queries/audits/above_average_team_turnover_18m_audit_20260910.sql`
- `queries/audits/above_average_team_turnover_termination_reconciliation_20260910.sql`

<!-- END evaluate-attrition-variable-run:above-average-team-turnover:above-average-team-turnover-v4-20260910-r13 -->
