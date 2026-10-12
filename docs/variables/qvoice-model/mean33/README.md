# Promedio de 33 preguntas comparables

<!-- BEGIN evaluate-attrition-variable:promedio-de-33-preguntas-comparables -->
## Conocimiento acumulado: Promedio de 33 preguntas comparables

_Actualizado por el assessment v4 `qvoice-model-20261008-mean33-v1` el 2026-10-08T09:52:25-06:00._

### Contexto del problema

- **Problema:** Determinar qué señales anuales de QVoice mejoran la predicción de salida voluntaria en Engineering.
- **Decisión / caso de uso:** Comparar el modelo B con componentes QVoice y controles de disponibilidad, sin modificar el modelo adoptado.
- **Outcome:** Salida voluntaria en los seis meses siguientes al snapshot.
- **Población:** Empleados regulares activos de Engineering, excluyendo RF360, en cada snapshot mensual.
- **Límite de conocimiento:** 2026-09-07
- **Rol de la variable:** candidate_variable
- **Relevancia:** El promedio comparable puede aportar contexto adicional, pero incluye Q4 y Q12 y requiere una ablacion.

### Definición y fuente evaluadas

- **Definición vigente:** Promedio de treinta y tres preguntas comparables: cien veces las respuestas favorables entre treinta y tres. Exige todos los binarios válidos y asigna seis bandas sin redondeo previo.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** Fuente no validada o externa: La lista exacta del playbook define los componentes, el denominador, las fronteras y la cohorte de la ablación.
- **Columnas:** M01, M02, M03, M04, M05, M06, M07, M08, M09, M10, M11, M12, M13, M14, M15, M16, M17, M18, M19, M20, M21, M22, M23, M24, M25, M26, M27, M28, M29, M30, M31, M32, M33
- **Grain:** Agregado por empleado-wave

### Relaciones con el portafolio

- El promedio contiene Q4/Q12.

### Resultado y evidencia agregada

- **Resultado:** Baja - exploratoria (6 puntos).
- **Scores:** Source=2, Definition=1, Coverage=0, Missingness=0, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** 68.0682%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Cumple.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Cumple.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Cumple.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- El coverage observable reciente está por debajo del mínimo de 70% para score 1.
- Missingness reciente supera el máximo de 30% para score 1.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.

**Acciones recomendadas**

- No se requiere acción inmediata; repetir la validación si cambia la fuente o definición.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Lograr al menos 3 observaciones consecutivas con >= 95% de coverage.

**SQL y evidencia trazable**

- `queries\profiles\qvoice-model-20261008-mean33-v1_01_promedio-de-33-preguntas-comparables_coverage.sql`
- `queries/audits/qvoice_model_mean33_20261008.sql`
- `queries/audits/qvoice_model_annual_lag_windows_20261008.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 3.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:promedio-de-33-preguntas-comparables -->

<!-- BEGIN evaluate-attrition-variable-run:promedio-de-33-preguntas-comparables:qvoice-model-20261006-mean33-v1 -->

### Historial de decisión — run `qvoice-model-20261006-mean33-v1`

_Registrado el 2026-10-06T13:18:52-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (6 puntos).

**Evolución del plan**

- Plan v3: Se explicita la conciliación del playbook antes de ejecutar la evidencia actual; el cálculo de Engineering conserva una población distinta.

**Validaciones y efecto observado**

- **source:** ¿Los 33 textos exactos tienen un encabezado único en los tres años? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El cálculo exacto y las seis bandas coinciden con una implementación independiente? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Se excluyen del promedio los incompletos sin excluirlos de las otras señales? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Las bandas se calculan sobre personas únicas de Engineering? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿El promedio era conocible en los snapshots de entrenamiento y evaluación? — resultado No cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿La recomendación del cuestionario principal permanece separada de la del bloque de salida? — resultado Cumple; impacto: Evidencia contextual para Definition; sin capacidad de aumentar el score.
- **consistency:** ¿Se reproducen los conteos, fórmulas y ventanas publicados al usar la población original? — resultado Cumple; impacto: Evidencia contextual para Consistency; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261006-mean33-v1_01_promedio-de-33-preguntas-comparables_coverage.sql`
- `queries/audits/qvoice_model_mean33_20261006.sql`

<!-- END evaluate-attrition-variable-run:promedio-de-33-preguntas-comparables:qvoice-model-20261006-mean33-v1 -->

<!-- BEGIN evaluate-attrition-variable-run:promedio-de-33-preguntas-comparables:qvoice-model-20261006-mean33-v1-r2 -->

### Historial de decisión — run `qvoice-model-20261006-mean33-v1-r2`

_Registrado el 2026-10-06T13:25:41-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (6 puntos).

**Evolución del plan**

- Plan v3: Se explicita la conciliación del playbook antes de ejecutar la evidencia actual; el cálculo de Engineering conserva una población distinta.

**Validaciones y efecto observado**

- **source:** ¿Los 33 textos exactos tienen un encabezado único en los tres años? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El cálculo exacto y las seis bandas coinciden con una implementación independiente? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Se excluyen del promedio los incompletos sin excluirlos de las otras señales? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Las bandas se calculan sobre personas únicas de Engineering? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿El promedio era conocible en los snapshots de entrenamiento y evaluación? — resultado No cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿La recomendación del cuestionario principal permanece separada de la del bloque de salida? — resultado Cumple; impacto: Evidencia contextual para Definition; sin capacidad de aumentar el score.
- **consistency:** ¿Se reproducen los conteos, fórmulas y ventanas publicados al usar la población original? — resultado Cumple; impacto: Evidencia contextual para Consistency; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261006-mean33-v1-r2_01_promedio-de-33-preguntas-comparables_coverage.sql`
- `queries/audits/qvoice_model_mean33_20261006.sql`

<!-- END evaluate-attrition-variable-run:promedio-de-33-preguntas-comparables:qvoice-model-20261006-mean33-v1-r2 -->

<!-- BEGIN evaluate-attrition-variable-run:promedio-de-33-preguntas-comparables:qvoice-model-20261008-mean33-v1 -->

### Historial de decisión — run `qvoice-model-20261008-mean33-v1`

_Registrado el 2026-10-08T09:52:25-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (6 puntos).

**Evolución del plan**

- Plan v3: Se amplía la redacción pública en español para el validador lingüístico; no cambian SQL, métricas ni umbrales.

**Validaciones y efecto observado**

- **source:** ¿Los 33 textos exactos tienen encabezado unico en los tres archivos? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿La formula y las seis bandas coinciden con una implementacion independiente? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Los incompletos quedan fuera del promedio sin salir de la cohorte general del modelo? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Las bandas se calculan sobre personas unicas de Engineering? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿La politica Y a Y+1 produce las ventanas declaradas antes de entrenar? — resultado Cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261008-mean33-v1_01_promedio-de-33-preguntas-comparables_coverage.sql`
- `queries/audits/qvoice_model_mean33_20261008.sql`
- `queries/audits/qvoice_model_annual_lag_windows_20261008.sql`

<!-- END evaluate-attrition-variable-run:promedio-de-33-preguntas-comparables:qvoice-model-20261008-mean33-v1 -->
