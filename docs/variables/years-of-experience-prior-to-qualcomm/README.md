# Years of experience prior to Qualcomm

<!-- BEGIN evaluate-attrition-variable:years-of-experience-prior-to-qualcomm -->
## Conocimiento acumulado: Years of experience prior to Qualcomm

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:33:11-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Employment history
- **Relevancia:** La experiencia previa distingue etapa profesional más allá del tenure en la compañía.

### Definición y fuente evaluadas

- **Definición vigente:** Años numéricos de experiencia laboral acumulados antes del empleo en Qualcomm.
- **Tipo semántico:** precomputed_metric
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** prior_qc_work_years
- **Grain:** Snapshot de empleado

### Relaciones con el portafolio

- Comparten count_window_time_since (shared_semantic_cue).
- Comparten flag_event (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta obtener lineage autoritativo y una reconciliación independiente de fórmula, componentes y tolerancia. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta obtener lineage autoritativo y una reconciliación independiente de fórmula, componentes y tolerancia.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y obtener lineage autoritativo y una reconciliación independiente de fórmula, componentes y tolerancia; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_13_years-of-experience-prior-to-qualcomm_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_13_years-of-experience-prior-to-qualcomm_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_13_years-of-experience-prior-to-qualcomm_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_13_years-of-experience-prior-to-qualcomm_prior-qc-work-years_report_top_values.sql`

### Evidencia activa: tasa anual de salida Voluntary por experiencia previa

#### Flujo histórico y alcance

El assessment v4 de agosto trató `prior_qc_work_years` como un campo numérico almacenado observado en snapshots mensuales y dejó pendiente la confirmación de su fórmula. La ejecución activa revalidó esa hipótesis para una vista descriptiva: partió de la población Employee/Regular/Active, reconstruyó cinco años fiscales completos (FY2021–FY2025), conservó las siete bandas predefinidas y atribuyó cada evento Voluntary a la última banda válida observada antes de `term_date`. Los eventos sin banda previa válida se conservaron en la reconciliación y no se reasignaron.

El entregable está clasificado como `internal_analysis`. El deck activo [attrition-43-variable-distributions-v2.html](../../../output/distribution/attrition-43-variable-distributions-v2.html) conserva el contenido heredado, inserta el slide 17 inmediatamente después de `Prior experience` y desplaza los slides heredados siguientes a 18–47. El resultado es evidencia descriptiva/asociativa para decidir una segmentación; no es causalidad, predicción individual ni score.

#### Validaciones ejecutadas

**Calendario fiscal y snapshots completos**

- **Pregunta:** ¿Los cinco años usados tienen exactamente doce snapshots y excluyen el snapshot futuro o un año parcial?
- **Motivo:** La comparación anual sólo es válida con la misma cobertura temporal en cada periodo.
- **Método:** Reconciliación agregada de `fiscal_year`, `fiscal_month`, `fis_mo_beg_dt` y `fis_mo_end_dt`, con corte `2026-09-11`.
- **Regla de aceptación:** Cinco años fiscales, doce fechas únicas por año, meses 1–12 y ninguna fecha posterior al corte.
- **Métricas observadas:** FY2021–FY2025; 60 snapshots; 12 meses por año; rango de último snapshot `2021-09-26` a `2025-09-28`; cero periodos futuros seleccionados.
- **Conclusión:** `pass`. FY2026 parcial y el snapshot futuro `2026-09-27` quedaron fuera.
- **Impacto en score:** No modifica el score vigente; respalda el uso descriptivo de la historia temporal.
- **Acción:** Mantener el corte y repetir esta auditoría si se amplía la ventana.

**Bandas, dominio y duplicados**

- **Pregunta:** ¿Las siete bandas son mutuamente excluyentes y exhaustivas para valores válidos de `prior_qc_work_years`?
- **Motivo:** Los valores inválidos no deben convertirse silenciosamente en cero ni en una banda de cola.
- **Método:** `CASE` explícito sobre valores no nulos `>= 0`, auditoría agregada de dominio y comprobación de duplicados empleado-snapshot.
- **Regla de aceptación:** Cero solapamientos, suma de bandas igual al dominio válido y cero filas duplicadas en el grain empleado-snapshot.
- **Métricas observadas:** 164 snapshots activos con valor negativo; 0 nulos; 0 fechas con duplicados; los negativos quedaron excluidos y documentados.
- **Conclusión:** `warning` por el dominio negativo observado, con bandas reproducibles para los valores válidos.
- **Impacto en score:** No eleva la definición ni la consistencia a 2; la definición del campo almacenado continúa pendiente.
- **Acción:** Confirmar con el dueño del dato la regla de dominio y el tratamiento histórico de valores negativos.

**Denominadores y privacidad**

- **Pregunta:** ¿Cada celda visible tiene doce denominadores mensuales completos y tamaño suficiente?
- **Motivo:** La tasa usa el promedio mensual del headcount activo y debe cumplir la regla de publicación agregada.
- **Método:** Malla año-mes-banda con headcount distinto, promedio mensual, mínimo mensual y empleados distintos anuales.
- **Regla de aceptación:** `months_with_headcount=12`, `min_monthly_headcount>=30` y `annual_distinct_employees>=30`.
- **Métricas observadas:** 35 celdas publicadas; 35/35 con 12 meses; mínimo anual distinto 2,736; mínimo mensual 2,209; 0 celdas suprimidas por privacidad.
- **Conclusión:** `pass`. Todas las celdas mostradas cumplen `n >= 30` sin reagrupación posterior.
- **Impacto en score:** No modifica el score vigente; confirma cobertura suficiente para esta vista agregada.
- **Acción:** Conservar los rangos fijos y volver a comprobar privacidad en cada nueva fecha de corte.

**Atribución y reconciliación de eventos Voluntary**

- **Pregunta:** ¿Las salidas Voluntary se pueden atribuir de forma temporal a una única banda válida previa?
- **Motivo:** Usar una observación posterior o la banda actual introduciría leakage y cambiaría el estimando.
- **Método:** Filtro de `term_date` conocido y `term_type=VOLUNTARY`, seguido de `ROW_NUMBER` sobre snapshots activos previos, ordenados de forma descendente.
- **Regla de aceptación:** La suma de bandas debe reconciliarse con los eventos Voluntary del año; los eventos sin banda previa deben quedar explícitos y sin reasignación.
- **Métricas observadas:** 12,631 eventos Voluntary; 12,327 atribuidos; 304 sin banda previa válida; cobertura por año FY2021–FY2025 de 87.6688%, 99.3946%, 99.8973%, 99.8746% y 99.8768%; cero eventos duplicados en las bandas.
- **Conclusión:** `warning` deliberado: la reconciliación de las bandas atribuidas es exacta, pero la cobertura no es 100% por left-censoring o valores previos inválidos.
- **Impacto en score:** No justifica score 2 para la definición; la fórmula temporal y el lineage aún requieren confirmación.
- **Acción:** Investigar las causas agregadas de los 304 eventos no atribuidos antes de interpretar diferencias como una comparación completa de salidas.

**Lineage y lenguaje de interpretación**

- **Pregunta:** ¿La vista demuestra cómo se calculó `prior_qc_work_years` en origen?
- **Motivo:** Una columna almacenada, su nombre o una distribución anterior no prueban componentes, traslapes, redondeo ni fecha efectiva.
- **Método:** Se separó la evidencia del campo almacenado de la evidencia de la tasa anual y se dejó trazabilidad a SQL y resultados hashados.
- **Regla de aceptación:** No elevar la definición a score 2 sin lineage autoritativo y reconciliación independiente sobre la población objetivo.
- **Métricas observadas:** La evidencia activa valida bandas, calendario, denominadores y atribución descriptiva, pero no reconstruye la fórmula de origen.
- **Conclusión:** La limitación permanece abierta; el campo debe seguir documentándose como stored/precomputed con lineage pendiente.
- **Impacto en score:** Se conserva `Definition=1` del assessment vigente.
- **Acción:** Obtener lineage autoritativo y repetir la validación independiente antes de usar la variable como feature SQL resuelta.

#### Artefactos y hashes

- SQL principal: `queries/audits/prior_experience_annual_voluntary_attrition_20260911.sql` — SHA-256 `143eae86c3230a2536208b846e9fb0da4e6baaab4448585b613baf51909c40cf`.
- SQL de brechas: `queries/audits/prior_experience_annual_voluntary_attrition_gap_20260911.sql` — SHA-256 `6ea7261704947c4e13bf753fb03bb77ecb949aa16ea65de379ff768f45870be6`.
- Resultado de la consulta principal: `11640256834d25fbaaae87cc7d7ac96840121c235c3644fa91476420b559e8ba`.
- Resultado de la auditoría de brechas: `0693705554a83c18f3d654c9db49dbb00942ecdaf07de10cb473d0fe233efed3`.
- Evidencia JSON: `output/distribution/json/attrition-43-variable-distributions-v2.prior-experience-annual-attrition-evidence-20260911.json` — SHA-256 `75bbcf2da8652065c9e2b512a50a7dd1233dc5494375964ef17a73a4fe026b7d`.
- Manifest activo: `output/distribution/json/attrition-43-variable-distributions-v2-manifest.json` — SHA-256 `3fcb595dd1f017eaa6cafd872ae6d217e6c5d66a0a8307303d8685b06f99be44`.
- HTML activo: `output/distribution/attrition-43-variable-distributions-v2.html` — SHA-256 `04ea6ce83d94002c13567571da45be76938749bce4b7d44f0afe332c5c04bf8e`.

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:years-of-experience-prior-to-qualcomm -->
