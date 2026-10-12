# Heartbeat — signos relativos de seis preguntas

<!-- BEGIN evaluate-attrition-variable:heartbeat-signos-relativos-de-seis-preguntas -->
## Conocimiento acumulado: Heartbeat — signos relativos de seis preguntas

_Actualizado por el assessment v4 `qvoice-model-20261006-heartbeat-v4` el 2026-10-07T07:54:26-06:00._

### Contexto del problema

- **Problema:** Determinar qué señales anuales de QVoice mejoran la predicción de salida voluntaria en Engineering.
- **Decisión / caso de uso:** Comparar el modelo B con componentes QVoice y controles de disponibilidad, sin modificar el modelo adoptado.
- **Outcome:** Salida voluntaria en los seis meses siguientes al snapshot.
- **Población:** Empleados regulares activos de Engineering, excluyendo RF360, en cada snapshot mensual.
- **Límite de conocimiento:** 2026-09-07
- **Rol de la variable:** candidate_variable
- **Relevancia:** La posición de cada respuesta respecto al promedio personal puede contener señal complementaria; no equivale al valor absoluto ni a importancia predictiva.

### Definición y fuente evaluadas

- **Definición vigente:** Signos de Q38/Q37/Q32/Q53/Q10/Q11 frente a la media personal de los 53 ítems ordinales, con al menos 38 respuestas 1–5 válidas. La definición no se transporta a un cuestionario distinto sin equivalencia.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** Fuente no validada o externa: La evidencia anterior es de 2026 YTD y usa una media personal. Los 52 ítems de 2025 no equivalen automáticamente a los 53 de 2026.
- **Columnas:** Q38, Q37, Q32, Q53, Q10, Q11
- **Grain:** Agregado por empleado-wave

### Relaciones con el portafolio

- No se documentaron relaciones contextuales adicionales.

### Resultado y evidencia agregada

- **Resultado:** Baja - exploratoria (6 puntos).
- **Scores:** Source=2, Definition=1, Coverage=0, Missingness=0, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** 29.0674%.
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
- Acreditar disponibilidad y repetir la evaluación temporal; no contar los meses replicados como waves independientes.

**SQL y evidencia trazable**

- `queries\profiles\qvoice-model-20261006-heartbeat-v4_01_heartbeat-signos-relativos-de-seis-preguntas_coverage.sql`
- `queries/audits/qvoice_model_heartbeat_20261006.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 5.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:heartbeat-signos-relativos-de-seis-preguntas -->

<!-- BEGIN evaluate-attrition-variable-run:heartbeat-signos-relativos-de-seis-preguntas:qvoice-model-20261006-heartbeat-v4 -->

### Historial de decisión — run `qvoice-model-20261006-heartbeat-v4`

_Registrado el 2026-10-07T07:54:26-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Baja - exploratoria (6 puntos).

**Evolución del plan**

- Plan v5: La primera conciliación confirmó fuente y cohortes, pero detectó diferencias de eventos. Se agrega una réplica del filtro temporal original para comprobar el efecto de incluir snapshots posteriores, conservando el corte vigente en todas las cifras principales.

**Validaciones y efecto observado**

- **source:** ¿Cuáles archivos contienen los 53 ítems ordinales que requiere la definición original? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El signo calculado por productos enteros coincide con la comparación contra la media personal? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Las 53 entradas del promedio personal son ordinales 1–5, incluidos los ítems fuera de los seis signos publicados? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Los signos enlazan sin duplicados a la población de Engineering? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿Hay dos periodos principales con cuestionario comparable y disponibilidad acreditada? — resultado No cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Se reproducen los 18 segmentos pregunta/signo publicados para 2026 con la misma población y ventana? — resultado Cumple; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\qvoice-model-20261006-heartbeat-v4_01_heartbeat-signos-relativos-de-seis-preguntas_coverage.sql`
- `queries/audits/qvoice_model_heartbeat_20261006.sql`

<!-- END evaluate-attrition-variable-run:heartbeat-signos-relativos-de-seis-preguntas:qvoice-model-20261006-heartbeat-v4 -->
