# Manager leaving

<!-- BEGIN evaluate-attrition-variable:manager-leaving -->
## Conocimiento acumulado: Manager leaving

_Actualizado por el assessment v4 `manager-leaving-consistency-join-validation-20260820-5` el 2026-08-20T22:19:44-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente un portafolio de variables de RH para determinar su utilidad, relación y preparación para el caso de uso configurado.
- **Decisión / caso de uso:** Medir disrupcion potencial posterior a la salida del manager.
- **Outcome:** Por confirmar.
- **Población:** Empleados regulares activos en cada snapshot mensual
- **Límite de conocimiento:** Solo eventos con term_date igual o anterior al cierre y observados en o antes del snapshot de prediccion.
- **Rol de la variable:** Manager movement
- **Relevancia:** El evento solo es utilizable si puede atribuirse al manager correcto sin informacion futura.

### Definición y fuente evaluadas

- **Definición vigente:** Exposicion time-safe a la terminacion del manager que supervisaba al empleado antes de la salida.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** employee_id, manager_employee_id, manager_effective_date, fis_mo_beg_dt, fis_mo_end_dt, worker_type, employee_type, active_status, is_termed, term_date, term_type, max_hire_rehire_date
- **Grain:** Empleado-snapshot mensual

### Relaciones con el portafolio

- No se documentaron relaciones contextuales adicionales.

### Resultado y evidencia agregada

- **Resultado:** Alta - lista para modelo (14 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=2, History=2, Join=2, Effort=1
- **Coverage reciente:** 99.998%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- Se cumplieron todos los requisitos v4 para este score cualitativo. Resultado de la prueba: Cumple.
- La prueba aporta contexto para interpretar el concepto, pero no es un requisito definitorio y no puede elevar el score.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- No se requiere acción inmediata; repetir la validación si cambia la fuente o definición.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\manager-leaving-consistency-join-validation-20260820-5_01_manager-leaving_coverage.sql`
- `queries/audits/manager_leaving_source_access_20260820.sql`
- `queries/audits/manager_leaving_all_terminations_consistency_v4_20260820.sql`
- `queries/audits/manager_leaving_join_reconciliation_v2_20260820.sql`
- `queries/audits/manager_leaving_consistency_reconciliation_v1_20260820.sql`
- `queries/audits/manager_leaving_same_snapshot_unmatched_v3_20260820.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
### Decisiones de evaluación vigentes

- **Autoría del plan:** codex_explicit.
- **Versiones de plan:** 7.
- **Revisión de suficiencia:** Hay brechas pendientes.

<!-- END evaluate-attrition-variable:manager-leaving -->

<!-- BEGIN evaluate-attrition-variable-run:manager-leaving:manager-leaving-consistency-join-validation-20260820-4 -->

### Historial de decisión — run `manager-leaving-consistency-join-validation-20260820-4`

_Registrado el 2026-08-20T22:15:15-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Media - utilizable con trabajo (12 puntos).

**Evolución del plan**

- Plan v6: La ejecución v5 completó la evidencia pero el validador final rechazó dos frases por no reconocerlas como narrativa española. Esta versión sólo corrige la redacción; conserva las mismas consultas, métricas y reglas de aceptación.

**Validaciones y efecto observado**

- **source:** ¿Existen la relación mensual y la fuente de terminaciones con todos los campos requeridos? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿All_terminations tiene llaves de evento únicas, fechas válidas y dominios estables durante la historia utilizable? — resultado Cumple; impacto: Consistency quedó en 1 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Cada terminación utilizable se atribuye de forma única al equipo observado antes de la salida? — resultado Cumple; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Por qué los campos mensuales no se utilizan como evento canónico? — resultado Informativa; impacto: Evidencia contextual para Consistency; sin capacidad de aumentar el score.
- **join:** ¿Los managers sin coincidencia exacta ocurren fuera de su historia observada o dentro de huecos mensuales? — resultado Cumple parcialmente; impacto: Join quedó en 1 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Esta validación decide cuántos meses permanece expuesto el empleado? — resultado Informativa; impacto: Evidencia contextual para Definition; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\manager-leaving-consistency-join-validation-20260820-4_01_manager-leaving_coverage.sql`
- `queries/audits/manager_leaving_source_access_20260820.sql`
- `queries/audits/manager_leaving_all_terminations_consistency_v4_20260820.sql`
- `queries/audits/manager_leaving_join_reconciliation_v2_20260820.sql`
- `queries/audits/manager_leaving_consistency_reconciliation_v1_20260820.sql`
- `queries/audits/manager_leaving_same_snapshot_unmatched_v3_20260820.sql`

<!-- END evaluate-attrition-variable-run:manager-leaving:manager-leaving-consistency-join-validation-20260820-4 -->

<!-- BEGIN evaluate-attrition-variable-run:manager-leaving:manager-leaving-consistency-join-validation-20260820-5 -->

### Historial de decisión — run `manager-leaving-consistency-join-validation-20260820-5`

_Registrado el 2026-08-20T22:19:44-06:00. Este registro conserva decisiones y evidencia explicada; no contiene razonamiento interno libre._

**Resultado:** Alta - lista para modelo (14 puntos).

**Evolución del plan**

- Plan v7: La ejecucion v6 demostro que las consultas y sus resultados eran validos, pero tambien revelo que el spec conservaba nombres de metricas de una ruta anterior. Esta revision alinea la puerta ejecutable con event_key_count y con las metricas reales del join seleccionado; no cambia las consultas ni las reglas sustantivas.

**Validaciones y efecto observado**

- **source:** ¿Existen la relacion mensual y la fuente de terminaciones con todos los campos requeridos? — resultado Cumple; impacto: Source quedó en 2 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿All_terminations tiene llaves de evento unicas, fechas validas y dominios estables durante la historia utilizable? — resultado Cumple; impacto: Consistency quedó en 2 de acuerdo con la evidencia y los límites v4.
- **join:** ¿Cada terminacion utilizable se atribuye de forma unica al equipo observado antes de la salida? — resultado Cumple; impacto: Join quedó en 2 de acuerdo con la evidencia y los límites v4.
- **consistency:** ¿Por que los campos mensuales no se utilizan como evento canonico? — resultado Informativa; impacto: Evidencia contextual para Consistency; sin capacidad de aumentar el score.
- **join:** ¿Los managers sin coincidencia exacta ocurren fuera de su historia observada o dentro de huecos mensuales? — resultado Cumple; impacto: Join quedó en 2 de acuerdo con la evidencia y los límites v4.
- **definition:** ¿Esta validacion decide cuantos meses permanece expuesto el empleado? — resultado Informativa; impacto: Evidencia contextual para Definition; sin capacidad de aumentar el score.

**Evidencia SQL agregada**

- `queries\profiles\manager-leaving-consistency-join-validation-20260820-5_01_manager-leaving_coverage.sql`
- `queries/audits/manager_leaving_source_access_20260820.sql`
- `queries/audits/manager_leaving_all_terminations_consistency_v4_20260820.sql`
- `queries/audits/manager_leaving_join_reconciliation_v2_20260820.sql`
- `queries/audits/manager_leaving_consistency_reconciliation_v1_20260820.sql`
- `queries/audits/manager_leaving_same_snapshot_unmatched_v3_20260820.sql`

<!-- END evaluate-attrition-variable-run:manager-leaving:manager-leaving-consistency-join-validation-20260820-5 -->

## Decisión de distribución — 2026-09-09

La decisión de negocio aprobó una ventana de exposición de seis meses y el
alcance estricto `Voluntary`. Para el snapshot del 2026-08-23, la feature se
deriva para empleados regulares activos con `employee_id` utilizable: se toma
el último vínculo empleado-manager anterior a `term_date`, se exige que el
manager tuviera `reg_non_intern_dir_reports > 0` en su último snapshot previo,
y la exposición se conserva aun si el empleado recibe un manager nuevo.

La distribución de presentación interna es `0/1+`: 49,198 de 50,043 empleados
no tenían una salida elegible de manager en la ventana y 845 (1.69%) tenían una
o más. Como el bucket `2+` no alcanza `n >= 30`, el conteo alternativo se
publica únicamente como `0/1+`; por claridad, se recomienda el flag binario
como feature primaria y el conteo sólo como sensibilidad.

No se usó una terminación futura del manager ni una salida futura del empleado
para derivar la feature. El resultado conserva 862 de 928 atribuciones
empleado-evento aunque el manager vigente al corte sea diferente, de acuerdo
con la política de reasignación aprobada. Esta decisión habilita la
distribución del slide; no sustituye una revalidación v4 independiente para
elevar `Definition` a 2.

**Evidencia trazable:**

- `config/manager_leaving_distribution_plan_v8_20260909.yaml`
- `queries/audits/manager_leaving_voluntary_6m_source_access_20260909.sql`
- `queries/audits/manager_leaving_voluntary_6m_distribution_20260909.sql`
- `output/distribution/json/manager-leaving-voluntary-6m-evidence-20260909.json`
