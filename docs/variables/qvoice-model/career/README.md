# Career goals — respuesta binaria

<!-- BEGIN evaluate-attrition-variable:career-goals-respuesta-binaria -->
## Conocimiento acumulado: Career goals - respuesta binaria

_Actualizado por el assessment v4 `qvoice-model-20261008-career-v2` el 2026-10-08T09:49:51-06:00._

### Contexto del problema

- **Problema:** Determinar qué señales anuales de QVoice mejoran la predicción de salida voluntaria en Engineering.
- **Decisión / caso de uso:** Comparar el modelo B con componentes QVoice y controles de disponibilidad, sin modificar el modelo adoptado.
- **Outcome:** Salida voluntaria en los seis meses siguientes al snapshot.
- **Población:** Empleados regulares activos de Engineering, excluyendo RF360, en cada snapshot mensual.
- **Límite de conocimiento:** 2026-09-07
- **Rol de la variable:** candidate_variable
- **Relevancia:** La percepcion de oportunidades de carrera puede aportar informacion adicional a Intent to Stay.

### Definición y fuente evaluadas

- **Definición vigente:** Respuesta favorable binaria al ítem de metas de carrera. La versión de 2024 incluye la palabra Overall y su transporte entre años se mantiene como sensibilidad exploratoria.
- **Tipo semántico:** survey
- **Tabla / fuente:** Fuente no validada o externa: Los encabezados exactos se versionan por año; la semejanza del texto no demuestra equivalencia semántica.
- **Columnas:** career
- **Grain:** Agregado por empleado-wave

### Relaciones con el portafolio

- No se documentaron relaciones contextuales adicionales.

### Resultado y evidencia agregada

- **Resultado:** Baja - exploratoria (8 puntos).
- **Scores:** Source=2, Definition=1, Coverage=1, Missingness=1, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** 79.3305%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- La definición no puede considerarse confirmada hasta confirmar elegibilidad, wave, codificación, comparabilidad y join temporal de la encuesta. Resultado de la prueba: No cumple.
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

- `queries\profiles\qvoice-model-20261008-career-v2_01_career-goals-respuesta-binaria_coverage.sql`
- `queries/audits/qvoice_model_career_20261008.sql`
- `queries/audits/qvoice_model_annual_lag_windows_20261008.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 3.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:career-goals-respuesta-binaria -->

<!-- BEGIN evaluate-attrition-variable-run:career-goals-respuesta-binaria:qvoice-model-20261006-career-v2 -->

### Historial de decisión — run `qvoice-model-20261006-career-v2`

_Registrado el 2026-10-06T13:12:55-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (8 puntos).

**Evolución del plan**

- Plan v3: Se precisa la redacción española de la regla de acceso y el destino Engineering. Los criterios, SQL y umbrales conservan el mismo significado.

**Validaciones y efecto observado**

- **source:** ¿Se encuentra exactamente un ítem binario de carrera con el texto declarado en cada año? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿La versión Overall de 2024 es equivalente a la de los dos años siguientes? — resultado No cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿El ítem mantiene dominio 0/1 sin convertir 255 en desfavorable? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿La comparación anual de carrera conserva un único enlace por persona en Engineering? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿Cuándo estuvieron disponibles las respuestas de carrera de cada año? — resultado No cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Se reproducen los conteos, fórmulas y ventanas publicados al usar la población original? — resultado No cumple; impacto: Evidencia contextual para Consistency; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261006-career-v2_01_career-goals-respuesta-binaria_coverage.sql`
- `queries/audits/qvoice_model_career_20261006.sql`

<!-- END evaluate-attrition-variable-run:career-goals-respuesta-binaria:qvoice-model-20261006-career-v2 -->

<!-- BEGIN evaluate-attrition-variable-run:career-goals-respuesta-binaria:qvoice-model-20261008-career-v2 -->

### Historial de decisión — run `qvoice-model-20261008-career-v2`

_Registrado el 2026-10-08T09:49:51-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (8 puntos).

**Evolución del plan**

- Plan v3: El validador lingüístico exige reglas de aceptación públicas más explícitas en español; no cambian SQL, métricas ni umbrales.

**Validaciones y efecto observado**

- **source:** ¿Existe exactamente un item binario de carrera por archivo? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿La redaccion Overall de 2024 esta confirmada como equivalente a 2025? — resultado No cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿El item conserva dominio 0/1 sin convertir 255 en no favorable? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El item enlaza de forma unica a Engineering? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿La politica Y a Y+1 produce las ventanas declaradas antes de entrenar? — resultado Cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261008-career-v2_01_career-goals-respuesta-binaria_coverage.sql`
- `queries/audits/qvoice_model_career_20261008.sql`
- `queries/audits/qvoice_model_annual_lag_windows_20261008.sql`

<!-- END evaluate-attrition-variable-run:career-goals-respuesta-binaria:qvoice-model-20261008-career-v2 -->
