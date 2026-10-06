# Intent to Stay items

<!-- BEGIN evaluate-attrition-variable:intent-to-stay-items -->
## Conocimiento acumulado: Intent to Stay items

_Actualizado por el assessment v4 `qvoice-excel-v4-20260826-1` el 2026-08-26T17:21:47-06:00._

### Contexto del problema

- **Problema:** Evaluar que formas historicas de QVoice pueden aportar senales utiles para entender attrition.
- **Decisión / caso de uso:** Priorizar variables QVoice binarias y ordinales para analisis longitudinal y modelado exploratorio de attrition.
- **Outcome:** Attrition posterior a la fecha conocida de la wave QVoice.
- **Población:** Respuestas QVoice disponibles en los workbooks raw; la elegibilidad oficial de workforce queda pendiente de reconciliacion.
- **Límite de conocimiento:** Fecha de la wave QVoice; no usar informacion posterior.
- **Rol de la variable:** candidate_variable
- **Relevancia:** Comparar la senal binaria historica de Intent to Stay con attrition posterior.

### Definición y fuente evaluadas

- **Definición vigente:** KPI Intent to Stay calculado como el promedio de las preguntas Q4 y Q12 definidas en survey_structure.xlsx, usando los componentes validos disponibles por empleado-wave.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** Fuente no validada o externa: survey_structure.xlsx define Q4 y Q12 como los dos componentes del KPI. Las waves antiguas pueden aportar solo Q4 y las recientes pueden tener ambas columnas pero respuestas parciales.
- **Columnas:** Emp ID, Snapshot Date o Recorded Date, Response Type, Region, Q4, Q12, *_favorable o *_FAV
- **Grain:** Employee-wave response aggregate

### Relaciones con el portafolio

- Son dos representaciones de los mismos items conceptuales.
- Comparten *_favorable o *_FAV (shared_source_column).
- Comparten Emp ID (shared_source_column).
- Comparten Q12 (shared_source_column).
- Comparten Q4 (shared_source_column).
- Comparten Region (shared_source_column).
- Comparten Response Type (shared_source_column).
- Comparten Snapshot Date o Recorded Date (shared_source_column).
- Comparten group_category_level (shared_semantic_cue).
- Comparten index_score_average (shared_semantic_cue).
- Comparten survey_external (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (10 puntos).
- **Scores:** Source=0, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 97.2656%.
- **Historia utilizable:** 80.0 meses.

**Hallazgos principales**

- La evidencia definitoria ejecutada no pasó o permanece pendiente. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Cumple.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Cumple.

**Limitaciones vigentes**

- La evidencia definitoria ejecutada no pasó o permanece pendiente.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.

**Acciones recomendadas**

- Resolver la regla pendiente o fallida, guardar la validación enfocada y repetir esta variable.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\qvoice-excel-v4-20260826-1_01_intent-to-stay-items_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 1.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:intent-to-stay-items -->

<!-- BEGIN evaluate-attrition-variable-run:intent-to-stay-items:qvoice-excel-v4-20260826-1 -->

### Historial de decisión — run `qvoice-excel-v4-20260826-1`

_Registrado el 2026-08-26T17:21:47-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (10 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿El diccionario y los encabezados de cada workbook resuelven Q4 y Q12 para Intent to Stay? — resultado Cumple; impacto: Source quedó en 0 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El promedio binario se calcula con Q4 y Q12 validos, distinguiendo respuestas completas de parciales? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿La disponibilidad de Q4/Q12 y el dominio binario se mantienen trazables entre waves? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El Excel conserva un grain unico de empleado-wave para esta respuesta? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-1_01_intent-to-stay-items_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826.sql`

<!-- END evaluate-attrition-variable-run:intent-to-stay-items:qvoice-excel-v4-20260826-1 -->

## Incidencia abierta de mapeo: QVoice marzo de 2023

_Validada el 2026-09-21. Este hallazgo corrige la interpretación de la cobertura; no modifica todavía el assessment, los scores ni el deck._

- **Pregunta:** ¿El `n=0` mostrado para Intent to Stay en la wave 2023 significa que no hubo respuestas a Q4 y Q12?
- **Evidencia documental:** `survey_structure.xlsx` define Intent to Stay con Q4 (`I see myself working at Qualcomm in a few years`) y Q12 (`I rarely think about looking for a new job with another company`).
- **Método:** revisión agregada y de encabezados de `March 2023 Pulse_raw data.xlsx`, hoja `Raw data`; se excluyeron las respuestas con `Response Type = EX Spam` y no se expusieron filas ni identificadores.
- **Resultado observado:** la fuente sí contiene ambas preguntas. De 7,011 respuestas `EX`, Q4 tiene 6,708 valores binarios válidos, Q12 tiene 6,603 y 6,556 tienen los dos componentes. Hay 303 filas `EX Spam` excluidas.
- **Causa:** la wave conserva los encabezados binarios con el texto plano de la pregunta (duplicados junto a la respuesta Likert), sin los sufijos `_favorable`, `_FAV` o `_S`. El resolvedor actual sólo admite esos sufijos para columnas binarias, por lo que no encuentra Q4 ni Q12 y produce artificialmente `n=0`.
- **Conclusión:** `n=0` en 2023 no representa ausencia de respuestas; representa una falla de mapeo de encabezados.
- **Acción requerida antes de volver a renderizar:** ajustar el resolvedor para reconocer la pareja binaria 0/1 de marzo de 2023 sin confundirla con la pareja Likert de texto, volver a ejecutar los agregados de Intent to Stay y revisar el resultado antes de modificar el slide.
