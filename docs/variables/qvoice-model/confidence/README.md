# Confidence — Q13 y Q17

<!-- BEGIN evaluate-attrition-variable:confidence-q13-y-q17 -->
## Conocimiento acumulado: Confidence — Q13 y Q17

_Actualizado por el assessment v4 `qvoice-model-20261008_full-confidence-v1` el 2026-10-08T11:56:46-06:00._

### Contexto del problema

- **Problema:** Determinar qué señales anuales de QVoice mejoran la predicción de salida voluntaria en Engineering.
- **Decisión / caso de uso:** Comparar el modelo B con componentes QVoice y controles de disponibilidad, sin modificar el modelo adoptado.
- **Outcome:** Salida voluntaria en los seis meses siguientes al snapshot.
- **Población:** Empleados regulares activos de Engineering, excluyendo RF360, en cada snapshot mensual.
- **Límite de conocimiento:** 2026-09-07
- **Rol de la variable:** candidate_variable
- **Relevancia:** La confianza en el futuro y en los cambios necesarios para competir puede complementar las percepciones individuales de carrera.

### Definición y fuente evaluadas

- **Definición vigente:** Binarios Q13, confianza en el futuro, y Q17, cambios necesarios para competir; no sustituir Q17 por la pregunta Q25 de liderazgo.
- **Tipo semántico:** survey
- **Tabla / fuente:** Fuente no validada o externa: El diccionario actual asigna Q13/Q17 a Confidence. Una interpretación habitual de confianza en liderazgo no reemplaza este mapping.
- **Columnas:** Q13, Q17
- **Grain:** Agregado por empleado-wave

### Relaciones con el portafolio

- No se documentaron relaciones contextuales adicionales.

### Resultado y evidencia agregada

- **Resultado:** Baja - exploratoria (8 puntos).
- **Scores:** Source=2, Definition=1, Coverage=1, Missingness=1, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** 80.5689%.
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

- `queries\profiles\qvoice-model-20261008_full-confidence-v1_01_confidence-q13-y-q17_coverage.sql`
- `queries/audits/qvoice_model_confidence_20261008_full.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 1.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:confidence-q13-y-q17 -->

<!-- BEGIN evaluate-attrition-variable-run:confidence-q13-y-q17:qvoice-model-20261006-confidence-v1 -->

### Historial de decisión — run `qvoice-model-20261006-confidence-v1`

_Registrado el 2026-10-06T13:41:46-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (8 puntos).

**Evolución del plan**

- Plan v2: Se precisa la redacción española antes de ejecutar la variable; se conservan los mismos criterios, consultas y umbrales.

**Validaciones y efecto observado**

- **source:** ¿El mapping exacto resuelve Q13/Q17 sin incorporar Q25? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Los dos componentes mantienen estados y validez independientes? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿El dominio 0/1 de ambas preguntas es estable en los archivos disponibles? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Ambas preguntas se vinculan sin multiplicación al workforce de Engineering? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿Existe evidencia de publicación antes de las predicciones? — resultado No cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261006-confidence-v1_01_confidence-q13-y-q17_coverage.sql`
- `queries/audits/qvoice_model_confidence_20261006.sql`

<!-- END evaluate-attrition-variable-run:confidence-q13-y-q17:qvoice-model-20261006-confidence-v1 -->

<!-- BEGIN evaluate-attrition-variable-run:confidence-q13-y-q17:qvoice-model-20261008_full-confidence-v1 -->

### Historial de decisión — run `qvoice-model-20261008_full-confidence-v1`

_Registrado el 2026-10-08T11:56:46-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (8 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿El mapping exacto resuelve Q13/Q17 sin incorporar Q25? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Los dos componentes mantienen estados y validez independientes? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿El dominio 0/1 de ambas preguntas es estable en los archivos disponibles? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Ambas preguntas se vinculan sin multiplicación al workforce de Engineering? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿La historia de confidence respeta la asignación anual aprobada y la versión de cada componente? — resultado Cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261008_full-confidence-v1_01_confidence-q13-y-q17_coverage.sql`
- `queries/audits/qvoice_model_confidence_20261008_full.sql`

<!-- END evaluate-attrition-variable-run:confidence-q13-y-q17:qvoice-model-20261008_full-confidence-v1 -->
