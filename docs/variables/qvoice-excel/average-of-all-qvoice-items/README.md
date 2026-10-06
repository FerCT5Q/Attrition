# Average of all Qvoice items

<!-- BEGIN evaluate-attrition-variable:average-of-all-qvoice-items -->
## Conocimiento acumulado: Average of all Qvoice items

_Actualizado por el assessment v4 `qvoice-excel-v4-20260826-1` el 2026-08-26T17:22:22-06:00._

### Contexto del problema

- **Problema:** Evaluar que formas historicas de QVoice pueden aportar senales utiles para entender attrition.
- **Decisión / caso de uso:** Priorizar variables QVoice binarias y ordinales para analisis longitudinal y modelado exploratorio de attrition.
- **Outcome:** Attrition posterior a la fecha conocida de la wave QVoice.
- **Población:** Respuestas QVoice disponibles en los workbooks raw; la elegibilidad oficial de workforce queda pendiente de reconciliacion.
- **Límite de conocimiento:** Fecha de la wave QVoice; no usar informacion posterior.
- **Rol de la variable:** candidate_variable
- **Relevancia:** Explorar el composite binario de QVoice frente a attrition posterior.

### Definición y fuente evaluadas

- **Definición vigente:** Promedio binario por empleado-wave de los items Favorable/FAV disponibles, con minimo tecnico de 70%.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** Fuente no validada o externa: El promedio no existe como campo directo; se recalcula desde el item set binario disponible por wave y requiere una regla de completitud y versionado.
- **Columnas:** Emp ID, Snapshot Date o Recorded Date, Response Type, Region, *_favorable o *_FAV
- **Grain:** Employee-wave derived aggregate

### Relaciones con el portafolio

- La normalizacion regional depende del composite binario base.
- Standardized / normalized within region depende de Average of all Qvoice items.
- Comparten *_favorable o *_FAV (shared_source_column).
- Comparten Emp ID (shared_source_column).
- Comparten Region (shared_source_column).
- Comparten Response Type (shared_source_column).
- Comparten Snapshot Date o Recorded Date (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten group_category_level (shared_semantic_cue).
- Comparten index_score_average (shared_semantic_cue).
- Comparten ratio_rate_percent (shared_semantic_cue).
- Comparten survey_external (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (11 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=1, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 96.7179%.
- **Historia utilizable:** 24.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: No cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: No cumple.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Cumple.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- Un patrón sistemático de missingness impide asignar score 2.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.

**Acciones recomendadas**

- No se requiere acción inmediata; repetir la validación si cambia la fuente o definición.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Investigar brechas por fecha y segmento elegible; objetivo <= 5% sin patrón sistemático.

**SQL y evidencia trazable**

- `queries\profiles\qvoice-excel-v4-20260826-1_05_average-of-all-qvoice-items_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 1.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:average-of-all-qvoice-items -->

<!-- BEGIN evaluate-attrition-variable-run:average-of-all-qvoice-items:qvoice-excel-v4-20260826-1 -->

### Historial de decisión — run `qvoice-excel-v4-20260826-1`

_Registrado el 2026-08-26T17:22:22-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (11 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿Los componentes binarios del composite estan disponibles en los workbooks raw? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El composite binario se puede recalcular con una regla de completitud explicita? — resultado No cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿El item set y el dominio del composite binario son estables entre waves? — resultado No cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El composite queda en un grain unico de empleado-wave antes de unirse a workforce? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-1_05_average-of-all-qvoice-items_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826.sql`

<!-- END evaluate-attrition-variable-run:average-of-all-qvoice-items:qvoice-excel-v4-20260826-1 -->
