# Co-location with manager

## Etiquetas de attrition retrospectivas del slide 36 — 2026-09-21

**Pregunta.** ¿Qué tasa de attrition voluntario corresponde a cada año fiscal
mostrado en las distribuciones de co-location con el manager, sin ocultar los
años recientes por falta de seguimiento futuro?

**Método y población.** Para cada FY2021–FY2026 se fija la cohorte de empleados
regulares activos con par empleado-manager y ubicación asignada observable en
el cierre del año fiscal anterior. La etiqueta del FY es el porcentaje de esa
cohorte con `term_type = 'VOLUNTARY'` y `term_date` en
`(baseline_snapshot_date, outcome_cutoff_date]`, hasta el cierre del FY
etiquetado. Se calculan dos reglas: mismo `office_site` normalizado, y mismo
`office_site` más misma `city` normalizada. Es un proxy de ubicación asignada,
no evidencia de presencia física.

**Regla de aceptación.** Se exige una ventana retrospectiva completa, cohorte
agregada de al menos 30, cero snapshots duplicados o mappings conflictivos, y
un resultado agregado apto para `presentation`. FY2021–FY2026 cumplen la
regla. FY2020 permanece `Not estimable`: no existe en la fuente el cierre FY2019
necesario para formar una ventana comparable.

**Evidencia.** La consulta agregada es
`queries/audits/v7_nav39_colocation_august_trailing_12m_attrition_20260921.sql`
(SHA-256 `9141B63C1B6A3813E71E9C710834055DC98856877EFB2B2CD9C3AF4049D00F93`),
ejecutada el 2026-09-21. El resultado congelado y sus diagnósticos están en
`output/distribution/json/attrition-43-variable-distributions-v7.nav39-colocation-trailing-12m-evidence-20260921.json`.
Las cohortes publicadas superan el umbral; no se detectaron duplicados ni
mappings conflictivos. Los managers sin match se excluyen de las cohortes
comparables y se conservan sólo como diagnóstico agregado. FY2024 contiene 371
días debido al año fiscal de 53 semanas de la fuente.

**Impacto.** Esto sólo actualiza las etiquetas descriptivas de attrition del
slide; no cambia el score de la variable ni prueba una relación causal.

## Seguimiento exploratorio de relación con attrition — 2026-08-17

Se probó una asociación descriptiva y time-safe, no causal. La feature se
calculó en el snapshot `t` comparando `office_site` normalizado de empleado y
manager activo; el outcome fue `term_type = 'Voluntary'` con `term_date` en el
intervalo `(t, t+1]`. No se usaron domicilios, códigos postales ni etiquetas de
sitio.

| Grupo | Employee-snapshots comparables | Tasa voluntaria mensual |
|---|---:|---:|
| Mismo `office_site` | 2,671,098 | 0.5062% |
| `office_site` distinto | 158,182 | 0.4293% |

La diferencia bruta es 0.0769 puntos porcentuales; no es estable en la misma
dirección en todos los años fiscales. Por ello sólo indica que vale la pena
probar la señal en un modelo longitudinal controlado por año fiscal, región,
rol, nivel, tenure y modalidad de trabajo. No cambia ningún score ni demuestra
causalidad.

SQL trazable: `queries/audits/co_location_voluntary_attrition_association_v2_20260817.sql`.

<!-- BEGIN evaluate-attrition-variable:co-location-with-manager -->
## Conocimiento acumulado: Co-location with manager

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:39:20-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Manager / workplace
- **Relevancia:** La co-location física puede influir en acceso al manager y experiencia local del equipo.

### Definición y fuente evaluadas

- **Definición vigente:** Empleado y manager activo comparten el mismo sitio de oficina no vacío en el mismo snapshot.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** employee_id, manager_employee_id, office_site, country
- **Grain:** Par empleado-manager

### Relaciones con el portafolio

- Comparten country (shared_source_column).
- Comparten employee_id (shared_source_column).
- Comparten manager_employee_id (shared_source_column).
- Comparten office_site (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten flag_event (shared_semantic_cue).
- Comparten manager_team_layers (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (10 puntos).
- **Scores:** Source=2, Definition=1, Coverage=1, Missingness=1, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 93.2625%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Pendiente.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- El coverage observable reciente está por debajo del umbral de 95% para score 2.
- Missingness reciente supera el máximo de 5% para score 2.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.

**Acciones recomendadas**

- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Resolver brechas de elegibilidad u observabilidad y repetir el perfil; objetivo >= 95%.
- Investigar brechas por fecha y segmento elegible; objetivo <= 5% sin patrón sistemático.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_34_co-location-with-manager_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:co-location-with-manager -->
