# Standardized / normalized within region

## Evidencia vigente para la lámina descriptiva

_Actualizada el 2026-09-10. Esta sección documenta una distribución agregada
para el deck; no modifica el assessment v4 histórico ni eleva su score._

- **Propósito:** describir la posición relativa de respondentes dentro de la
  Región almacenada y la misma ola QVoice. No representa a toda la plantilla,
  no usa un denominador de workforce y no afirma una asociación con attrition.
- **Población y grain:** un participante por ola con `33/33` flags binarios
  estrictamente comparables válidos y `Region` no vacía; agregado
  participante-ola. `Response Type` no se interpreta como flag de completitud.
- **Cálculo:** `raw_score = 100 × favorable_items / 33`; para cada
  `Region × wave`, `z = (raw_score − media regional-ola) / desviación estándar
  poblacional regional-ola`.
- **Ventana y comparabilidad:** Jan-2024, Jan-2025 y Jan-2026; los 33 ítems
  son la intersección estricta estable de los 52, 52 y 53 flags binarios de las
  tres olas. No se usa similitud textual ni mapping fuzzy.
- **Resultado agregado:** 5 cohortes región-ola en cada ola (15 en total),
  todas con `n ≥ 30`; el mínimo observado fue 2,305. Las poblaciones
  normalizadas fueron 27,563, 30,342 y 33,067 respondentes. No hubo región
  faltante, duplicados, conflictos, valores binarios inválidos ni cohortes con
  desviación estándar cero.
- **Publicación:** se muestran sólo las bandas `< −1.0`, `−1.0–<−0.5`,
  `−0.5–<0.5`, `0.5–<1.0` y `≥ 1.0`, cada una con `n ≥ 30`. El JSON congelado
  no conserva identificadores, filas, respuestas, puntajes individuales ni
  etiquetas regionales.

La evidencia ejecutable se genera con
`tools/build_qvoice_normalized_region_evidence.py` y se valida nuevamente al
renderizar el deck. Si una puerta falla, la lámina conserva el estado de
soporte y no publica una distribución.

<!-- BEGIN evaluate-attrition-variable:standardized-normalized-within-region -->
## Conocimiento acumulado: Standardized / normalized within region

_Actualizado por el assessment v4 `qvoice-excel-v4-20260826-1` el 2026-08-26T17:22:44-06:00._

### Contexto del problema

- **Problema:** Evaluar que formas historicas de QVoice pueden aportar senales utiles para entender attrition.
- **Decisión / caso de uso:** Priorizar variables QVoice binarias y ordinales para analisis longitudinal y modelado exploratorio de attrition.
- **Outcome:** Attrition posterior a la fecha conocida de la wave QVoice.
- **Población:** Respuestas QVoice disponibles en los workbooks raw; la elegibilidad oficial de workforce queda pendiente de reconciliacion.
- **Límite de conocimiento:** Fecha de la wave QVoice; no usar informacion posterior.
- **Rol de la variable:** candidate_variable
- **Relevancia:** Explorar el z-score regional del composite binario frente a attrition posterior.

### Definición y fuente evaluadas

- **Definición vigente:** Z-score poblacional del composite binario dentro de cohortes Region-wave de al menos 30.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** Fuente no validada o externa: El z-score depende del composite binario, de Region y de cohortes de al menos 30; ninguno de esos criterios tiene lineage de feature gobernado en Excel.
- **Columnas:** Emp ID, Snapshot Date o Recorded Date, Response Type, Region, *_favorable o *_FAV
- **Grain:** Employee-wave-region derived aggregate

### Relaciones con el portafolio

- La normalizacion regional depende del composite binario base.
- Standardized / normalized within region depende de Average of all Qvoice items.
- Comparten *_favorable o *_FAV (shared_source_column).
- Comparten Emp ID (shared_source_column).
- Comparten Region (shared_source_column).
- Comparten Response Type (shared_source_column).
- Comparten Snapshot Date o Recorded Date (shared_source_column).
- Comparten group_category_level (shared_semantic_cue).
- Comparten index_score_average (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (11 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=1, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 96.7179%.
- **Historia utilizable:** 24.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Cumple.
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

- `queries\profiles\qvoice-excel-v4-20260826-1_07_standardized-normalized-within-region_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 1.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:standardized-normalized-within-region -->

<!-- BEGIN evaluate-attrition-variable-run:standardized-normalized-within-region:qvoice-excel-v4-20260826-1 -->

### Historial de decisión — run `qvoice-excel-v4-20260826-1`

_Registrado el 2026-08-26T17:22:44-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (11 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿Estan disponibles los componentes binarios y Region para normalizar? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El z-score binario se puede recalcular por Region y wave con cohortes de al menos 30? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Las cohortes regionales y el item set se mantienen consistentes entre waves? — resultado No cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El z-score conserva un grain unico de empleado-wave-region antes del join a workforce? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-excel-v4-20260826-1_07_standardized-normalized-within-region_coverage.sql`
- `queries/audits/qvoice_excel_source_inventory_20260826.sql`
- `queries/audits/qvoice_excel_definition_audit_20260826.sql`
- `queries/audits/qvoice_excel_consistency_audit_20260826.sql`
- `queries/audits/qvoice_excel_join_grain_audit_20260826.sql`

<!-- END evaluate-attrition-variable-run:standardized-normalized-within-region:qvoice-excel-v4-20260826-1 -->
