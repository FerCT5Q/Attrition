# Intent to Stay items

<!-- BEGIN evaluate-attrition-variable:intent-to-stay-items -->
## Conocimiento acumulado: Intent to Stay items

_Actualizado por el assessment v4 `qvoice-excel-v4-20260826-2-final2` el 2026-08-26T19:48:36-06:00._

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

- **Resultado:** Sensible / restringida (9 puntos).
- **Scores:** Source=0, Definition=1, Coverage=2, Missingness=1, Consistency=1, History=2, Join=1, Effort=1
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
- Un patrón sistemático de missingness impide asignar score 2.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.

**Acciones recomendadas**

- Resolver la regla pendiente o fallida, guardar la validación enfocada y repetir esta variable.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Investigar brechas por fecha y segmento elegible; objetivo <= 5% sin patrón sistemático.

**SQL y evidencia trazable**

- `queries\profiles\qvoice-excel-v4-20260826-2-final2_01_intent-to-stay-items_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826-2.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826-2.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 1.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:intent-to-stay-items -->

<!-- BEGIN evaluate-attrition-variable-run:intent-to-stay-items:qvoice-excel-v4-20260826-2-final -->

### Historial de decisión — run `qvoice-excel-v4-20260826-2-final`

_Registrado el 2026-08-26T19:44:53-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (9 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿El diccionario y los encabezados de cada workbook resuelven Q4 y Q12 para Intent to Stay? — resultado Cumple; impacto: Source quedó en 0 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El promedio binario se calcula con Q4 y Q12 validos, distinguiendo respuestas completas de parciales? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿La disponibilidad de Q4/Q12 y el dominio binario se mantienen trazables entre waves? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El Excel conserva un grain unico de empleado-wave para esta respuesta? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-2-final_01_intent-to-stay-items_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826-2.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826-2.sql`

<!-- END evaluate-attrition-variable-run:intent-to-stay-items:qvoice-excel-v4-20260826-2-final -->

<!-- BEGIN evaluate-attrition-variable-run:intent-to-stay-items:qvoice-excel-v4-20260826-2-final2 -->

### Historial de decisión — run `qvoice-excel-v4-20260826-2-final2`

_Registrado el 2026-08-26T19:48:36-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (9 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿El diccionario y los encabezados de cada workbook resuelven Q4 y Q12 para Intent to Stay? — resultado Cumple; impacto: Source quedó en 0 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El promedio binario se calcula con Q4 y Q12 validos, distinguiendo respuestas completas de parciales? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿La disponibilidad de Q4/Q12 y el dominio binario se mantienen trazables entre waves? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El Excel conserva un grain unico de empleado-wave para esta respuesta? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-2-final2_01_intent-to-stay-items_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826-2.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826-2.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826-2.sql`

<!-- END evaluate-attrition-variable-run:intent-to-stay-items:qvoice-excel-v4-20260826-2-final2 -->

## Visual 2024–2026: Favorable / No favorable

Actualizado el 2026-09-22 para los slides QVoice 21 y 22 del deck V7. Esta
nota documenta una regla de visualización agregada; no cambia los scores v4 ni
convierte la definición pendiente en una definición aprobada.

- **Pregunta y propósito:** mostrar si la attrition posterior difiere entre
  respuestas Favorable y No favorable, manteniendo una cohorte consistente
  entre cada barra y su tasa.
- **Regla de display:** se requieren respuestas binarias válidas en ambas
  componentes Q4 y Q12. `Favorable` significa Q4=1 y Q12=1; `No favorable`
  significa que al menos una de las dos es 0. Las respuestas parciales y los
  valores faltantes, inválidos o sentinel `255` se omiten del par de barras.
- **Método y evidencia:** los encabezados se resolvieron exactamente una vez
  por workbook con `header_base`, sin fuzzy matching ni sustitución de
  sinónimos. La llave de participante se usó sólo en memoria para deduplicar
  y para un join temporal agregado con workforce. La evidencia es
  `output/distribution/json/qvoice-favorable-unfavorable-attrition-evidence-20260921.json`;
  la ventana y unicidad del baseline se auditan en
  `queries/audits/qvoice_favorable_unfavorable_attrition_window_audit_20260921.sql`.
- **Ventana de outcome:** Jan-2024 y Jan-2025 usan terminaciones estrictamente
  `VOLUNTARY` durante los 12 meses posteriores al inicio de la wave. Jan-2026
  usa el mismo tipo de cohorte hasta 2026-09-27 y se etiqueta como YTD, no
  anualizada.
- **Resultado y límites:** los dos grupos son mutuamente excluyentes, suman
  100% dentro de la cohorte vinculada de cada año y todas las cohortes visibles
  cumplen `n >= 30`. La regla de negocio para el promedio con respuestas
  parciales sigue pendiente; por eso el visual excluye parciales y no se usa
  como evidencia para elevar Definition, Consistency o Join a 2.
