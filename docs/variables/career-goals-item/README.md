# Career goals item

<!-- BEGIN evaluate-attrition-variable:career-goals-item -->
## Conocimiento acumulado: Career goals item

_Actualizado por el assessment v4 `qvoice-excel-v4-20260826-2-final2` el 2026-08-26T19:48:51-06:00._

### Contexto del problema

- **Problema:** Evaluar que formas historicas de QVoice pueden aportar senales utiles para entender attrition.
- **Decisión / caso de uso:** Priorizar variables QVoice binarias y ordinales para analisis longitudinal y modelado exploratorio de attrition.
- **Outcome:** Attrition posterior a la fecha conocida de la wave QVoice.
- **Población:** Respuestas QVoice disponibles en los workbooks raw; la elegibilidad oficial de workforce queda pendiente de reconciliacion.
- **Límite de conocimiento:** Fecha de la wave QVoice; no usar informacion posterior.
- **Rol de la variable:** candidate_variable
- **Relevancia:** Evaluar la senal binaria de career goals frente a attrition posterior.

### Definición y fuente evaluadas

- **Definición vigente:** Respuesta binaria de career goals por empleado-wave.
- **Tipo semántico:** survey
- **Tabla / fuente:** Fuente no validada o externa: El item binario existe desde el longitudinal y en 2024-2026, aunque su wording cambia entre waves.
- **Columnas:** Emp ID, Snapshot Date o Recorded Date, Response Type, Region, career goals *_favorable o *_FAV
- **Grain:** Employee-wave response aggregate

### Relaciones con el portafolio

- Son dos representaciones del item de career goals.
- Comparten Emp ID (shared_source_column).
- Comparten Region (shared_source_column).
- Comparten Response Type (shared_source_column).
- Comparten Snapshot Date o Recorded Date (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten group_category_level (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (10 puntos).
- **Scores:** Source=2, Definition=1, Coverage=1, Missingness=1, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 90.027%.
- **Historia utilizable:** 80.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta confirmar elegibilidad, wave, codificación, comparabilidad y join temporal de la encuesta. Resultado de la prueba: Cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: No cumple.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Cumple.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta confirmar elegibilidad, wave, codificación, comparabilidad y join temporal de la encuesta.
- El coverage observable reciente está por debajo del umbral de 95% para score 2.
- Un patrón sistemático de missingness impide asignar score 2.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.

**Acciones recomendadas**

- No se requiere acción inmediata; repetir la validación si cambia la fuente o definición.
- Aprobar la definición y confirmar elegibilidad, wave, codificación, comparabilidad y join temporal de la encuesta; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Resolver brechas de elegibilidad u observabilidad y repetir el perfil; objetivo >= 95%.

**SQL y evidencia trazable**

- `queries\profiles\qvoice-excel-v4-20260826-2-final2_03_career-goals-item_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826-2.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826-2.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 1.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:career-goals-item -->

<!-- BEGIN evaluate-attrition-variable-run:career-goals-item:qvoice-excel-v4-20260826-2-final -->

### Historial de decisión — run `qvoice-excel-v4-20260826-2-final`

_Registrado el 2026-08-26T19:45:09-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (10 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿La fuente Excel contiene el item binario de career goals? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El item de career goals tiene respuestas validas en el dominio 0/1? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿El wording y el dominio del item de career goals son comparables entre waves? — resultado No cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El Excel conserva una fila interna por empleado-wave para career goals? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-2-final_03_career-goals-item_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826-2.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826-2.sql`

<!-- END evaluate-attrition-variable-run:career-goals-item:qvoice-excel-v4-20260826-2-final -->

<!-- BEGIN evaluate-attrition-variable-run:career-goals-item:qvoice-excel-v4-20260826-2-final2 -->

### Historial de decisión — run `qvoice-excel-v4-20260826-2-final2`

_Registrado el 2026-08-26T19:48:51-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (10 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿La fuente Excel contiene el item binario de career goals? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El item de career goals tiene respuestas validas en el dominio 0/1? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿El wording y el dominio del item de career goals son comparables entre waves? — resultado No cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El Excel conserva una fila interna por empleado-wave para career goals? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-2-final2_03_career-goals-item_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826-2.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826-2.sql`

<!-- END evaluate-attrition-variable-run:career-goals-item:qvoice-excel-v4-20260826-2-final2 -->

## Visual 2024–2026: Favorable / No favorable

Actualizado el 2026-09-22 para los slides QVoice 21 y 22 del deck V7. Esta
nota registra la operación de display agregada y no modifica los scores v4 de
la variable.

- **Pregunta y propósito:** comparar la distribución de la respuesta Career
  Goals con la attrition voluntaria posterior de cada cohorte QVoice.
- **Regla de display:** `Favorable` es el valor binario almacenado `1` y `No
  favorable` el valor `0`; se omiten blancos, inválidos y sentinel `255`.
  Cada par usa como denominador únicamente las respuestas de ese item que
  también enlazan al snapshot activo Regular anterior a la wave.
- **Método y evidencia:** el header binario se resolvió exactamente una vez
  por workbook, sin fuzzy matching. La evidencia agregada es
  `output/distribution/json/qvoice-favorable-unfavorable-attrition-evidence-20260921.json`;
  la ventana de outcome y la unicidad del snapshot se validan en
  `queries/audits/qvoice_favorable_unfavorable_attrition_window_audit_20260921.sql`.
- **Ventana de outcome:** Jan-2024 y Jan-2025 usan 12 meses completos de
  terminaciones estrictamente `VOLUNTARY` posteriores a la wave. Jan-2026
  llega sólo a 2026-09-27 y se presenta como YTD, sin anualizar.
- **Resultado y límites:** los grupos son mutuamente excluyentes, suman 100%
  dentro de cada cohorte vinculada y todos cumplen `n >= 30`. El item de 2024
  inicia con “Overall” y el de 2025–2026 no; el slide muestra cada wave como
  su propia mezcla de respuestas, no como una tendencia normalizada. Esa
  diferencia de wording permanece como límite de Definition/Consistency.
