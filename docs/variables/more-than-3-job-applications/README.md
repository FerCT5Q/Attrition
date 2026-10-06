# More than 3 job applications

<!-- BEGIN evaluate-attrition-variable:more-than-3-job-applications -->
## Conocimiento acumulado: More than 3 job applications

_Actualizado por el assessment v4 `more-than-3-job-applications-trailing-6m-20260907-v4` el 2026-09-07T21:27:01-06:00._

### Contexto del problema

- **Problema:** Evaluar una definición explícita de movilidad interna intensa para análisis longitudinal de attrition sin usar información posterior al snapshot.
- **Decisión / caso de uso:** Comprobar si un flag de cuatro o más solicitudes internas únicas en seis meses puede distribuirse de forma agregada y pasar a evaluación para el modelo de attrition.
- **Outcome:** Attrition voluntario posterior al snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual.
- **Límite de conocimiento:** Cierre del snapshot mensual. Sólo application_date menor o igual a ese cierre puede contribuir a la feature.
- **Rol de la variable:** Applications / internal mobility
- **Relevancia:** Una acumulación de solicitudes internas puede señalar búsqueda activa de movilidad, sujeto a validación de fuente y privacidad.

### Definición y fuente evaluadas

- **Definición vigente:** Flag candidato igual a uno cuando el empleado acumula cuatro o más requisiciones internas únicas con cand_applied=1 durante los seis meses calendario previos al cierre del snapshot.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.applications
- **Columnas:** employee_id, candidate_id, cand_applied, application_date, req_id
- **Grain:** Empleado-snapshot; conteo móvil de requisiciones

### Relaciones con el portafolio

- No se documentaron relaciones contextuales adicionales.

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (5 puntos).
- **Scores:** Source=1, Definition=1, Coverage=0, Missingness=0, Consistency=1, History=0, Join=1, Effort=1
- **Coverage reciente:** 49.8414%.
- **Historia utilizable:** 0.0 meses.

**Hallazgos principales**

- La evidencia definitoria ejecutada no pasó o permanece pendiente. Resultado de la prueba: Cumple parcialmente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Cumple parcialmente.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Cumple parcialmente.
- No existe una racha estable que califique como historia utilizable. Resultado de la prueba: No cumple.

**Limitaciones vigentes**

- La evidencia definitoria ejecutada no pasó o permanece pendiente.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- El coverage observable reciente está por debajo del mínimo de 70% para score 1.
- Missingness reciente supera el máximo de 30% para score 1.

**Acciones recomendadas**

- Resolver la regla pendiente o fallida, guardar la validación enfocada y repetir esta variable.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Lograr al menos 3 observaciones consecutivas con >= 95% de coverage.
- Resolver brechas de elegibilidad u observabilidad y repetir el perfil; objetivo >= 95%.

**SQL y evidencia trazable**

- `queries\profiles\more-than-3-job-applications-trailing-6m-20260907-v4_01_more-than-3-job-applications_coverage.sql`
- `queries/audits/more-than-3-job-applications-trailing-6m-preflight3-20260907_portfolio_metadata.sql`
- `queries/audits/more_than_three_job_applications_trailing_6m_source_dedup_20260907.sql`
- `queries/audits/more_than_three_job_applications_trailing_6m_employee_linkage_20260907.sql`
- `queries/audits/more_than_three_job_applications_trailing_6m_time_safe_linkage_20260907.sql`
- `queries/audits/more_than_three_job_applications_trailing_6m_boundary_recalculation_v2_20260907.sql`
- `queries/audits/more_than_three_job_applications_trailing_6m_join_20260907.sql`
- `queries/audits/more_than_three_job_applications_trailing_6m_feed_freshness_20260907.sql`
- `queries/profiles/more_than_three_job_applications_trailing_6m_annual_distribution_20260907.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 4.
- **Revisión de suficiencia:** Hay brechas pendientes.

### Nota sobre la revisión interna de aplicaciones

La excepción visual autorizada para compartir la distribución anual agregada
con Julia (`internal_analysis`) sólo permite revisar conteos exploratorios, aun
cuando algún bucket sea menor de `n=30`. No cambia el assessment v4, el score,
el catálogo de variables ni la decisión de producción; tampoco convierte esta
variable en una feature aprobada ni permite datos individuales, requisiciones o
acceso de managers.

<!-- END evaluate-attrition-variable:more-than-3-job-applications -->

<!-- BEGIN evaluate-attrition-variable-run:more-than-3-job-applications:more-than-3-job-applications-trailing-6m-20260907-v4 -->

### Historial de decisión — run `more-than-3-job-applications-trailing-6m-20260907-v4`

_Registrado el 2026-09-07T21:27:01-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Sensible / restringida (5 puntos).

**Evolución del plan**

- Plan v4: El perfil preliminar contenía positivos mensuales inferiores a la cohorte mínima de privacidad. Se suprimen esas celdas y se añade una distribución anual que sólo publica años con al menos 30 positivos.

**Validaciones y efecto observado**

- **source:** ¿La fuente contiene eventos fechados y requisiciones utilizables para el conteo propuesto? — resultado Cumple parcialmente; impacto: Source quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Qué fracción del feed cand_applied=1 se puede vincular realmente a empleados? — resultado Cumple parcialmente; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El denominador de vínculo al feed evita usar una fila futura respecto al snapshot? — resultado Cumple parcialmente; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿El flag de seis meses se reproduce sin diferencias y excluye eventos futuros? — resultado Cumple parcialmente; impacto: Definition quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿El grain empleado-snapshot es único y qué proporción de la población puede vincularse al feed? — resultado Cumple parcialmente; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **history:** ¿El feed llega hasta el periodo más reciente de snapshots para interpretar la distribución actual? — resultado No cumple; impacto: History quedó en 0 de acuerdo con la evidencia y los límites v4.
- **coverage:** ¿Qué distribución anual publicable resulta del flag candidato? — resultado No cumple; impacto: Coverage quedó en 0 de acuerdo con la evidencia y los límites v4.

**Evidencia SQL agregada**

- `queries\profiles\more-than-3-job-applications-trailing-6m-20260907-v4_01_more-than-3-job-applications_coverage.sql`
- `queries/audits/more-than-3-job-applications-trailing-6m-preflight3-20260907_portfolio_metadata.sql`
- `queries/audits/more_than_three_job_applications_trailing_6m_source_dedup_20260907.sql`
- `queries/audits/more_than_three_job_applications_trailing_6m_employee_linkage_20260907.sql`
- `queries/audits/more_than_three_job_applications_trailing_6m_time_safe_linkage_20260907.sql`
- `queries/audits/more_than_three_job_applications_trailing_6m_boundary_recalculation_v2_20260907.sql`
- `queries/audits/more_than_three_job_applications_trailing_6m_join_20260907.sql`
- `queries/audits/more_than_three_job_applications_trailing_6m_feed_freshness_20260907.sql`
- `queries/profiles/more_than_three_job_applications_trailing_6m_annual_distribution_20260907.sql`

<!-- END evaluate-attrition-variable-run:more-than-3-job-applications:more-than-3-job-applications-trailing-6m-20260907-v4 -->
