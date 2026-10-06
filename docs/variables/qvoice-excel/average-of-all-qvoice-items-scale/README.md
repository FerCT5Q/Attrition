# Average of all Qvoice items-scale

<!-- BEGIN evaluate-attrition-variable:average-of-all-qvoice-items-scale -->
## Conocimiento acumulado: Average of all Qvoice items-scale

_Actualizado por el assessment v4 `qvoice-excel-v4-20260826-1` el 2026-08-26T17:22:32-06:00._

### Contexto del problema

- **Problema:** Evaluar que formas historicas de QVoice pueden aportar senales utiles para entender attrition.
- **Decisión / caso de uso:** Priorizar variables QVoice binarias y ordinales para analisis longitudinal y modelado exploratorio de attrition.
- **Outcome:** Attrition posterior a la fecha conocida de la wave QVoice.
- **Población:** Respuestas QVoice disponibles en los workbooks raw; la elegibilidad oficial de workforce queda pendiente de reconciliacion.
- **Límite de conocimiento:** Fecha de la wave QVoice; no usar informacion posterior.
- **Rol de la variable:** candidate_variable
- **Relevancia:** Explorar el composite ordinal 1-5 de QVoice frente a attrition posterior.

### Definición y fuente evaluadas

- **Definición vigente:** Promedio ordinal 1-5 por empleado-wave de los items scale disponibles, con minimo tecnico de 70%.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** Fuente no validada o externa: El composite ordinal se recalcula desde las columnas 1-5 de 2025-2026 y no tiene lineage autoritativo ni historia suficiente.
- **Columnas:** Emp ID, Recorded Date, Response Type, Region, *_1-5 scale
- **Grain:** Employee-wave derived aggregate

### Relaciones con el portafolio

- La normalizacion ordinal depende del composite 1-5 base.
- Standardized / normalized within region-scale depende de Average of all Qvoice items-scale.
- Comparten *_1-5 scale (shared_source_column).
- Comparten Emp ID (shared_source_column).
- Comparten Recorded Date (shared_source_column).
- Comparten Region (shared_source_column).
- Comparten Response Type (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten group_category_level (shared_semantic_cue).
- Comparten index_score_average (shared_semantic_cue).
- Comparten ratio_rate_percent (shared_semantic_cue).
- Comparten survey_external (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (10 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** 97.4638%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: No cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: No cumple.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Cumple.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- No existe una racha estable que califique como historia utilizable.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.

**Acciones recomendadas**

- No se requiere acción inmediata; repetir la validación si cambia la fuente o definición.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Lograr al menos 3 observaciones consecutivas con >= 95% de coverage.

**SQL y evidencia trazable**

- `queries\profiles\qvoice-excel-v4-20260826-1_06_average-of-all-qvoice-items-scale_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 1.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:average-of-all-qvoice-items-scale -->

<!-- BEGIN evaluate-attrition-variable-run:average-of-all-qvoice-items-scale:qvoice-excel-v4-20260826-1 -->

### Historial de decisión — run `qvoice-excel-v4-20260826-1`

_Registrado el 2026-08-26T17:22:32-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (10 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿Los componentes ordinales del composite estan disponibles en los workbooks raw? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El composite 1-5 se puede recalcular con una regla de completitud explicita? — resultado No cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿El item set 1-5 y su rango son estables entre 2025 y 2026? — resultado No cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El composite 1-5 queda en un grain unico de empleado-wave? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-1_06_average-of-all-qvoice-items-scale_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826.sql`

<!-- END evaluate-attrition-variable-run:average-of-all-qvoice-items-scale:qvoice-excel-v4-20260826-1 -->
