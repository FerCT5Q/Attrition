# Workplace Connection items-scale

<!-- BEGIN evaluate-attrition-variable:workplace-connection-items-scale -->
## Conocimiento acumulado: Workplace Connection items-scale

_Actualizado por el assessment v4 `qvoice-excel-v4-20260826-2-final2` el 2026-08-26T19:50:54-06:00._

### Contexto del problema

- **Problema:** Evaluar que formas historicas de QVoice pueden aportar senales utiles para entender attrition.
- **Decisión / caso de uso:** Priorizar variables QVoice binarias y ordinales para analisis longitudinal y modelado exploratorio de attrition.
- **Outcome:** Attrition posterior a la fecha conocida de la wave QVoice.
- **Población:** Respuestas QVoice disponibles en los workbooks raw; la elegibilidad oficial de workforce queda pendiente de reconciliacion.
- **Límite de conocimiento:** Fecha de la wave QVoice; no usar informacion posterior.
- **Rol de la variable:** candidate_variable
- **Relevancia:** Comparar la senal ordinal 1-5 de Workplace Connection, calculada con sus preguntas componentes, con attrition posterior.

### Definición y fuente evaluadas

- **Definición vigente:** KPI Workplace Connection ordinal calculado como promedio de Q5, Q6 y Q7 en escala 1-5.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** Fuente no validada o externa: La forma 1-5 debe resolver el mismo texto de Q5, Q6 y Q7 y tiene historia corta.
- **Columnas:** Emp ID, Recorded Date, Response Type, Region, Q5, Q6, Q7, *_1-5 scale
- **Grain:** Employee-wave response aggregate

### Relaciones con el portafolio

- Comparten *_1-5 scale (shared_source_column).
- Comparten Emp ID (shared_source_column).
- Comparten Q5 (shared_source_column).
- Comparten Q6 (shared_source_column).
- Comparten Q7 (shared_source_column).
- Comparten Recorded Date (shared_source_column).
- Comparten Region (shared_source_column).
- Comparten Response Type (shared_source_column).
- Comparten group_category_level (shared_semantic_cue).
- Comparten index_score_average (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (4 puntos).
- **Scores:** Source=0, Definition=1, Coverage=0, Missingness=0, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** 67.4837%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- La evidencia definitoria ejecutada no pasó o permanece pendiente. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Cumple.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Cumple.

**Limitaciones vigentes**

- La evidencia definitoria ejecutada no pasó o permanece pendiente.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- El coverage observable reciente está por debajo del mínimo de 70% para score 1.
- Missingness reciente supera el máximo de 30% para score 1.

**Acciones recomendadas**

- Resolver la regla pendiente o fallida, guardar la validación enfocada y repetir esta variable.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Resolver brechas de elegibilidad u observabilidad y repetir el perfil; objetivo >= 95%.

**SQL y evidencia trazable**

- `queries\profiles\qvoice-excel-v4-20260826-2-final2_12_workplace-connection-items-scale_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826-2.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826-2.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 1.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:workplace-connection-items-scale -->

<!-- BEGIN evaluate-attrition-variable-run:workplace-connection-items-scale:qvoice-excel-v4-20260826-2-final -->

### Historial de decisión — run `qvoice-excel-v4-20260826-2-final`

_Registrado el 2026-08-26T19:46:22-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (4 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿Los encabezados 1-5 resuelven Q5, Q6 y Q7 por workbook? — resultado Cumple; impacto: Source quedó en 0 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El promedio ordinal usa solo valores 1-5 validos y separa respuestas parciales? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿El dominio ordinal y el item set de Q5/Q6/Q7 se mantienen trazables? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿La forma ordinal conserva un grain unico de empleado-wave? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-2-final_12_workplace-connection-items-scale_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826-2.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826-2.sql`

<!-- END evaluate-attrition-variable-run:workplace-connection-items-scale:qvoice-excel-v4-20260826-2-final -->

<!-- BEGIN evaluate-attrition-variable-run:workplace-connection-items-scale:qvoice-excel-v4-20260826-2-final2 -->

### Historial de decisión — run `qvoice-excel-v4-20260826-2-final2`

_Registrado el 2026-08-26T19:50:54-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (4 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿Los encabezados 1-5 resuelven Q5, Q6 y Q7 por workbook? — resultado Cumple; impacto: Source quedó en 0 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El promedio ordinal usa solo valores 1-5 validos y separa respuestas parciales? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿El dominio ordinal y el item set de Q5/Q6/Q7 se mantienen trazables? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿La forma ordinal conserva un grain unico de empleado-wave? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-2-final2_12_workplace-connection-items-scale_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826-2.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826-2.sql`

<!-- END evaluate-attrition-variable-run:workplace-connection-items-scale:qvoice-excel-v4-20260826-2-final2 -->
