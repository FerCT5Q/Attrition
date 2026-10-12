# Wellbeing — versiones histórica y completa

<!-- BEGIN evaluate-attrition-variable:wellbeing-versiones-hist-rica-y-completa -->
## Conocimiento acumulado: Wellbeing — versiones histórica y completa

_Actualizado por el assessment v4 `qvoice-model-20261008_full-wellbeing-v1` el 2026-10-08T11:55:14-06:00._

### Contexto del problema

- **Problema:** Determinar qué señales anuales de QVoice mejoran la predicción de salida voluntaria en Engineering.
- **Decisión / caso de uso:** Comparar el modelo B con componentes QVoice y controles de disponibilidad, sin modificar el modelo adoptado.
- **Outcome:** Salida voluntaria en los seis meses siguientes al snapshot.
- **Población:** Empleados regulares activos de Engineering, excluyendo RF360, en cada snapshot mensual.
- **Límite de conocimiento:** 2026-09-07
- **Rol de la variable:** candidate_variable
- **Relevancia:** La energía durante y después del trabajo y el estrés pueden aportar información diferente; Q9 no integra la versión histórica.

### Definición y fuente evaluadas

- **Definición vigente:** Versión histórica Q8/Q10/Q11 y versión completa Q8/Q9/Q10/Q11; Q9 está ausente en 2024. La energía durante y después del trabajo y el estrés se mantienen como componentes separados.
- **Tipo semántico:** survey
- **Tabla / fuente:** Fuente no validada o externa: Q9 añade capacidad percibida para mejorar bienestar; no es intercambiable con los tres ítems históricos ni con Q47 de balance.
- **Columnas:** Q8, Q9, Q10, Q11
- **Grain:** Agregado por empleado-wave

### Relaciones con el portafolio

- No se documentaron relaciones contextuales adicionales.

### Resultado y evidencia agregada

- **Resultado:** Baja - exploratoria (8 puntos).
- **Scores:** Source=2, Definition=1, Coverage=1, Missingness=1, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** 81.0437%.
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

- `queries\profiles\qvoice-model-20261008_full-wellbeing-v1_01_wellbeing-versiones-hist-rica-y-completa_coverage.sql`
- `queries/audits/qvoice_model_wellbeing_20261008_full.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 1.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:wellbeing-versiones-hist-rica-y-completa -->

<!-- BEGIN evaluate-attrition-variable-run:wellbeing-versiones-hist-rica-y-completa:qvoice-model-20261006-wellbeing-v2 -->

### Historial de decisión — run `qvoice-model-20261006-wellbeing-v2`

_Registrado el 2026-10-06T13:39:45-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (8 puntos).

**Evolución del plan**

- Plan v3: Se aclara en español la población para el validador de narrativa; se conservan la población efectiva, las consultas, las métricas y los umbrales de v2.

**Validaciones y efecto observado**

- **source:** ¿Se resuelven Q8/Q10/Q11 y se conserva la ausencia de Q9 en 2024? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿La versión con Q9 conserva una completitud distinta de Q8/Q10/Q11? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Energía y estrés mantienen un dominio válido sin interpretar faltantes como bajo bienestar? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿La cobertura y asociación de Wellbeing usan un enlace único a Engineering? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿Las versiones de Wellbeing tienen disponibilidad y componentes anteriores a cada corte? — resultado No cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261006-wellbeing-v2_01_wellbeing-versiones-hist-rica-y-completa_coverage.sql`
- `queries/audits/qvoice_model_wellbeing_20261006.sql`

<!-- END evaluate-attrition-variable-run:wellbeing-versiones-hist-rica-y-completa:qvoice-model-20261006-wellbeing-v2 -->

<!-- BEGIN evaluate-attrition-variable-run:wellbeing-versiones-hist-rica-y-completa:qvoice-model-20261008_full-wellbeing-v1 -->

### Historial de decisión — run `qvoice-model-20261008_full-wellbeing-v1`

_Registrado el 2026-10-08T11:55:14-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (8 puntos).

**Evolución del plan**

- Plan v1: plan inicial antes de ejecutar evidencia agregada.

**Validaciones y efecto observado**

- **source:** ¿Se resuelven Q8/Q10/Q11 y se conserva la ausencia de Q9 en 2024? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿La versión con Q9 conserva una completitud distinta de Q8/Q10/Q11? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Energía y estrés mantienen un dominio válido sin interpretar faltantes como bajo bienestar? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿La cobertura y asociación de Wellbeing usan un enlace único a Engineering? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿La historia de wellbeing respeta la asignación anual aprobada y la versión de cada componente? — resultado Cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261008_full-wellbeing-v1_01_wellbeing-versiones-hist-rica-y-completa_coverage.sql`
- `queries/audits/qvoice_model_wellbeing_20261008_full.sql`

<!-- END evaluate-attrition-variable-run:wellbeing-versiones-hist-rica-y-completa:qvoice-model-20261008_full-wellbeing-v1 -->
