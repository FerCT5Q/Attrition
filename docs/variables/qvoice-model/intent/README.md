# Intent to Stay — Q4 y Q12

<!-- BEGIN evaluate-attrition-variable:intent-to-stay-q4-y-q12 -->
## Conocimiento acumulado: Intent to Stay - Q4 y Q12

_Actualizado por el assessment v4 `qvoice-model-20261008-intent-v2` el 2026-10-08T09:45:17-06:00._

### Contexto del problema

- **Problema:** Determinar qué señales anuales de QVoice mejoran la predicción de salida voluntaria en Engineering.
- **Decisión / caso de uso:** Comparar el modelo B con componentes QVoice y controles de disponibilidad, sin modificar el modelo adoptado.
- **Outcome:** Salida voluntaria en los seis meses siguientes al snapshot.
- **Población:** Empleados regulares activos de Engineering, excluyendo RF360, en cada snapshot mensual.
- **Límite de conocimiento:** 2026-09-07
- **Rol de la variable:** candidate_variable
- **Relevancia:** Las preguntas de permanencia pueden aportar informacion incremental al modelo B.

### Definición y fuente evaluadas

- **Definición vigente:** Respuestas binarias a Q4 y Q12, evaluadas por separado y en conjunto. La categoría ambas favorables exige dos respuestas válidas y representa la percepción declarada de permanencia.
- **Tipo semántico:** survey
- **Tabla / fuente:** Fuente no validada o externa: Q4 y Q12 son las dos señales priorizadas de permanencia en el playbook; se conservan por separado y como conjunción sin imputar faltantes.
- **Columnas:** Q4, Q12
- **Grain:** Agregado por empleado-wave

### Relaciones con el portafolio

- El promedio contiene Q4/Q12.

### Resultado y evidencia agregada

- **Resultado:** Baja - exploratoria (8 puntos).
- **Scores:** Source=2, Definition=1, Coverage=1, Missingness=1, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** 80.3767%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta confirmar elegibilidad, wave, codificación, comparabilidad y join temporal de la encuesta. Resultado de la prueba: Cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Cumple.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Cumple.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta confirmar elegibilidad, wave, codificación, comparabilidad y join temporal de la encuesta.
- El coverage observable reciente está por debajo del umbral de 95% para score 2.
- Missingness reciente supera el máximo de 5% para score 2.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.

**Acciones recomendadas**

- No se requiere acción inmediata; repetir la validación si cambia la fuente o definición.
- Aprobar la definición y confirmar elegibilidad, wave, codificación, comparabilidad y join temporal de la encuesta; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Lograr al menos 3 observaciones consecutivas con >= 95% de coverage.

**SQL y evidencia trazable**

- `queries\profiles\qvoice-model-20261008-intent-v2_01_intent-to-stay-q4-y-q12_coverage.sql`
- `queries/audits/qvoice_model_intent_20261008.sql`
- `queries/audits/qvoice_model_annual_lag_windows_20261008.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 2.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:intent-to-stay-q4-y-q12 -->

<!-- BEGIN evaluate-attrition-variable-run:intent-to-stay-q4-y-q12:qvoice-model-20261006-intent-v2-r2 -->

### Historial de decisión — run `qvoice-model-20261006-intent-v2-r2`

_Registrado el 2026-10-06T13:03:11-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Por definir (8 puntos).

**Evolución del plan**

- Plan v3: La primera conciliación detecta un baseline actual menor al publicado. Se contrasta el filtro original con los totales nuevos, sin cambiar los conteos históricos.

**Validaciones y efecto observado**

- **source:** ¿Los tres archivos resuelven de forma única los encabezados binarios de Q4 y Q12? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Ambas favorables exige Q4=1 y Q12=1 y excluye respuestas parciales? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Se distinguen 0/1, vacío, 255, inválido y pregunta ausente? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Cada respuesta enlaza como máximo con una persona de Engineering en la foto previa? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿Se acredita la fecha en que Q4 y Q12 pudieron conocerse antes de cada predicción? — resultado No cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Se reproducen los conteos, fórmulas y ventanas publicados al usar la población original? — resultado No cumple; impacto: Evidencia contextual para Consistency; sin capacidad de aumentar el score.
- **join:** ¿El filtro original confirma los nuevos denominadores y su diferencia frente al JSON publicado? — resultado Cumple; impacto: Evidencia contextual para Join; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261006-intent-v2-r2_01_intent-to-stay-q4-y-q12_coverage.sql`
- `queries/audits/qvoice_model_intent_20261006.sql`
- `queries/audits/qvoice_model_baseline_reconciliation_20261006.sql`

<!-- END evaluate-attrition-variable-run:intent-to-stay-q4-y-q12:qvoice-model-20261006-intent-v2-r2 -->

<!-- BEGIN evaluate-attrition-variable-run:intent-to-stay-q4-y-q12:qvoice-model-20261006-intent-v2-r3 -->

### Historial de decisión — run `qvoice-model-20261006-intent-v2-r3`

_Registrado el 2026-10-06T13:15:30-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (8 puntos).

**Evolución del plan**

- Plan v3: La primera conciliación detecta un baseline actual menor al publicado. Se contrasta el filtro original con los totales nuevos, sin cambiar los conteos históricos.

**Validaciones y efecto observado**

- **source:** ¿Los tres archivos resuelven de forma única los encabezados binarios de Q4 y Q12? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Ambas favorables exige Q4=1 y Q12=1 y excluye respuestas parciales? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Se distinguen 0/1, vacío, 255, inválido y pregunta ausente? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Cada respuesta enlaza como máximo con una persona de Engineering en la foto previa? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿Se acredita la fecha en que Q4 y Q12 pudieron conocerse antes de cada predicción? — resultado No cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Se reproducen los conteos, fórmulas y ventanas publicados al usar la población original? — resultado No cumple; impacto: Evidencia contextual para Consistency; sin capacidad de aumentar el score.
- **join:** ¿El filtro original confirma los nuevos denominadores y su diferencia frente al JSON publicado? — resultado Cumple; impacto: Evidencia contextual para Join; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261006-intent-v2-r3_01_intent-to-stay-q4-y-q12_coverage.sql`
- `queries/audits/qvoice_model_intent_20261006.sql`
- `queries/audits/qvoice_model_baseline_reconciliation_20261006.sql`

<!-- END evaluate-attrition-variable-run:intent-to-stay-q4-y-q12:qvoice-model-20261006-intent-v2-r3 -->

<!-- BEGIN evaluate-attrition-variable-run:intent-to-stay-q4-y-q12:qvoice-model-20261008-intent-v2 -->

### Historial de decisión — run `qvoice-model-20261008-intent-v2`

_Registrado el 2026-10-08T09:45:17-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (8 puntos).

**Evolución del plan**

- Plan v2: Se corrige la redacción pública para cumplir el contrato en español; no cambian las preguntas, SQL ni reglas de aceptación.

**Validaciones y efecto observado**

- **source:** ¿Los tres archivos resuelven de forma unica Q4 y Q12? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Ambas favorables exige Q4=1 y Q12=1 y excluye respuestas parciales? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Se distinguen 0, 1, vacio, 255, invalido y pregunta ausente? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Cada respuesta enlaza como maximo con una persona de Engineering en el baseline? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿La politica Y a Y+1 produce las ventanas declaradas antes de entrenar? — resultado Cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261008-intent-v2_01_intent-to-stay-q4-y-q12_coverage.sql`
- `queries/audits/qvoice_model_intent_20261008.sql`
- `queries/audits/qvoice_model_annual_lag_windows_20261008.sql`

<!-- END evaluate-attrition-variable-run:intent-to-stay-q4-y-q12:qvoice-model-20261008-intent-v2 -->
