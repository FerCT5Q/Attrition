# Wellbeing items

<!-- BEGIN evaluate-attrition-variable:wellbeing-items -->
## Conocimiento acumulado: Wellbeing items

_Actualizado por el assessment v4 `qvoice-excel-v4-20260826-2-final2` el 2026-08-26T19:51:25-06:00._

### Contexto del problema

- **Problema:** Evaluar que formas historicas de QVoice pueden aportar senales utiles para entender attrition.
- **Decisión / caso de uso:** Priorizar variables QVoice binarias y ordinales para analisis longitudinal y modelado exploratorio de attrition.
- **Outcome:** Attrition posterior a la fecha conocida de la wave QVoice.
- **Población:** Respuestas QVoice disponibles en los workbooks raw; la elegibilidad oficial de workforce queda pendiente de reconciliacion.
- **Límite de conocimiento:** Fecha de la wave QVoice; no usar informacion posterior.
- **Rol de la variable:** candidate_variable
- **Relevancia:** Comparar la senal binaria historica de Wellbeing, calculada con sus preguntas componentes, con attrition posterior.

### Definición y fuente evaluadas

- **Definición vigente:** KPI Wellbeing calculado como promedio de Q8, Q9, Q10 y Q11 segun survey_structure.xlsx.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** Fuente no validada o externa: El diccionario define cuatro componentes de Wellbeing y el conjunto puede cambiar entre waves.
- **Columnas:** Emp ID, Snapshot Date o Recorded Date, Response Type, Region, Q8, Q9, Q10, Q11, *_favorable o *_FAV
- **Grain:** Employee-wave response aggregate

### Relaciones con el portafolio

- Comparten *_favorable o *_FAV (shared_source_column).
- Comparten Emp ID (shared_source_column).
- Comparten Q10 (shared_source_column).
- Comparten Q11 (shared_source_column).
- Comparten Q8 (shared_source_column).
- Comparten Q9 (shared_source_column).
- Comparten Region (shared_source_column).
- Comparten Response Type (shared_source_column).
- Comparten Snapshot Date o Recorded Date (shared_source_column).
- Comparten group_category_level (shared_semantic_cue).
- Comparten index_score_average (shared_semantic_cue).
- Comparten survey_external (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (9 puntos).
- **Scores:** Source=0, Definition=1, Coverage=2, Missingness=1, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 97.982%.
- **Historia utilizable:** 24.0 meses.

**Hallazgos principales**

- La evidencia definitoria ejecutada no pasó o permanece pendiente. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Cumple.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Cumple.

**Limitaciones vigentes**

- La evidencia definitoria ejecutada no pasó o permanece pendiente.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- Un patrón sistemático de missingness impide asignar score 2.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.

**Acciones recomendadas**

- Resolver la regla pendiente o fallida, guardar la validación enfocada y repetir esta variable.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Investigar brechas por fecha y segmento elegible; objetivo <= 5% sin patrón sistemático.

**SQL y evidencia trazable**

- `queries\profiles\qvoice-excel-v4-20260826-2-final2_13_wellbeing-items_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826-2.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826-2.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 1.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:wellbeing-items -->

<!-- BEGIN evaluate-attrition-variable-run:wellbeing-items:qvoice-excel-v4-20260826-2-final -->

### Historial de decisión — run `qvoice-excel-v4-20260826-2-final`

_Registrado el 2026-08-26T19:46:30-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (9 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿El diccionario y los workbooks resuelven Q8, Q9, Q10 y Q11 para Wellbeing? — resultado Cumple; impacto: Source quedó en 0 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El promedio binario de Wellbeing distingue respuestas completas, parciales y sin componente? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿El dominio y el conjunto Q8-Q11 son consistentes entre waves? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Wellbeing conserva una fila agregada por empleado-wave? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-2-final_13_wellbeing-items_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826-2.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826-2.sql`

<!-- END evaluate-attrition-variable-run:wellbeing-items:qvoice-excel-v4-20260826-2-final -->

<!-- BEGIN evaluate-attrition-variable-run:wellbeing-items:qvoice-excel-v4-20260826-2-final2 -->

### Historial de decisión — run `qvoice-excel-v4-20260826-2-final2`

_Registrado el 2026-08-26T19:51:25-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (9 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿El diccionario y los workbooks resuelven Q8, Q9, Q10 y Q11 para Wellbeing? — resultado Cumple; impacto: Source quedó en 0 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El promedio binario de Wellbeing distingue respuestas completas, parciales y sin componente? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿El dominio y el conjunto Q8-Q11 son consistentes entre waves? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Wellbeing conserva una fila agregada por empleado-wave? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-2-final2_13_wellbeing-items_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826-2.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826-2.sql`

<!-- END evaluate-attrition-variable-run:wellbeing-items:qvoice-excel-v4-20260826-2-final2 -->
