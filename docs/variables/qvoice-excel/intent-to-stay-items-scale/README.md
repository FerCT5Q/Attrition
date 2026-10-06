# Intent to Stay items-scale

<!-- BEGIN evaluate-attrition-variable:intent-to-stay-items-scale -->
## Conocimiento acumulado: Intent to Stay items-scale

_Actualizado por el assessment v4 `qvoice-excel-v4-20260826-1` el 2026-08-26T17:21:56-06:00._

### Contexto del problema

- **Problema:** Evaluar que formas historicas de QVoice pueden aportar senales utiles para entender attrition.
- **Decisión / caso de uso:** Priorizar variables QVoice binarias y ordinales para analisis longitudinal y modelado exploratorio de attrition.
- **Outcome:** Attrition posterior a la fecha conocida de la wave QVoice.
- **Población:** Respuestas QVoice disponibles en los workbooks raw; la elegibilidad oficial de workforce queda pendiente de reconciliacion.
- **Límite de conocimiento:** Fecha de la wave QVoice; no usar informacion posterior.
- **Rol de la variable:** candidate_variable
- **Relevancia:** Comparar la senal ordinal 1-5 de Intent to Stay con attrition posterior.

### Definición y fuente evaluadas

- **Definición vigente:** KPI Intent to Stay calculado como el promedio ordinal de las preguntas Q4 y Q12 definidas en survey_structure.xlsx, usando los componentes validos disponibles por empleado-wave.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** Fuente no validada o externa: survey_structure.xlsx define Q4 y Q12 como los dos componentes del KPI. La forma 1-5 solo aparece en 2025-2026 y debe conservar la brecha entre respuestas completas y parciales.
- **Columnas:** Emp ID, Recorded Date, Response Type, Region, Q4, Q12, *_1-5 scale
- **Grain:** Employee-wave response aggregate

### Relaciones con el portafolio

- Son dos representaciones de los mismos items conceptuales.
- Comparten *_1-5 scale (shared_source_column).
- Comparten Emp ID (shared_source_column).
- Comparten Q12 (shared_source_column).
- Comparten Q4 (shared_source_column).
- Comparten Recorded Date (shared_source_column).
- Comparten Region (shared_source_column).
- Comparten Response Type (shared_source_column).
- Comparten group_category_level (shared_semantic_cue).
- Comparten index_score_average (shared_semantic_cue).
- Comparten survey_external (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (9 puntos).
- **Scores:** Source=1, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** 97.8511%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Cumple.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Cumple.

**Limitaciones vigentes**

- La fuente o su ruta completa de acceso aún no están confirmadas para todos los componentes requeridos.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- No existe una racha estable que califique como historia utilizable.

**Acciones recomendadas**

- Confirmar propietario, tablas, columnas, permisos y vigencia de la fuente; después repetir la auditoría de disponibilidad.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Lograr al menos 3 observaciones consecutivas con >= 95% de coverage.

**SQL y evidencia trazable**

- `queries\profiles\qvoice-excel-v4-20260826-1_02_intent-to-stay-items-scale_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 1.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:intent-to-stay-items-scale -->

<!-- BEGIN evaluate-attrition-variable-run:intent-to-stay-items-scale:qvoice-excel-v4-20260826-1 -->

### Historial de decisión — run `qvoice-excel-v4-20260826-1`

_Registrado el 2026-08-26T17:21:56-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (9 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿El diccionario y los encabezados de cada workbook resuelven Q4 y Q12 en la forma 1-5? — resultado Cumple; impacto: Source quedó en 1 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El promedio ordinal se calcula con Q4 y Q12 validos, distinguiendo respuestas completas de parciales? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿La disponibilidad de Q4/Q12 y el dominio 1-5 son trazables entre sus waves disponibles? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El Excel conserva un grain unico de empleado-wave para la escala? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-1_02_intent-to-stay-items-scale_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826.sql`

<!-- END evaluate-attrition-variable-run:intent-to-stay-items-scale:qvoice-excel-v4-20260826-1 -->
