# Major inflection points

## Definición propuesta y cálculo revisado

_Esta sección recoge la definición de trabajo acordada después del assessment histórico. Es contexto humano pendiente de validación; todavía no modifica los scores ni sustituye una nueva ejecución v4._

`Major inflection points` representa un mes en el que una organización experimenta una cantidad de movimientos internos inusualmente alta frente a su propio comportamiento reciente. Se calcularía por snapshot y por alcance organizacional —por ejemplo, compañía, unidad, función o equipo— y después se asignaría a los empleados que pertenecían a ese alcance al cierre del snapshot.

No se interpreta como un cambio de domicilio personal. Los movimientos candidatos para el cálculo son:

- cambio de manager;
- transferencia interna;
- cambio de job family;
- cambio de cost center;
- cambio de ubicación de trabajo, conservado como componente separado hasta confirmar su semántica y distinguir una reubicación organizacional de otros cambios administrativos.

Un empleado se cuenta una sola vez en el mes aunque tenga más de un tipo de movimiento. Cuando existan flag y fecha, el movimiento debe asignarse al mes de la fecha efectiva y ambos campos deben reconciliarse antes de usarlo.

### Componente estadístico

Para cada alcance organizacional `s` y snapshot mensual `t`:

```text
movement_rate(s,t) = empleados regulares activos con al menos un movimiento calificable en el mes
                     -----------------------------------------------------------------------------
                     empleados regulares activos del alcance en el snapshot

movement_zscore(s,t) = [movement_rate(s,t) - promedio de los 24 snapshots anteriores]
                       ---------------------------------------------------------------
                       desviación estándar de los 24 snapshots anteriores
```

La ventana usa exclusivamente los 24 snapshots anteriores: no incluye el mes actual ni meses futuros. La clasificación propuesta es:

- `movement_zscore < 1.5`: comportamiento normal;
- `1.5 <= movement_zscore < 2.0`: movimiento elevado;
- `movement_zscore >= 2.0`: punto de inflexión mayor.

Se conserva el `movement_zscore` continuo además de la clasificación. Como regla conservadora pendiente de validación, no se forzará una clasificación estadística cuando no existan 24 snapshots previos comparables o cuando la desviación estándar sea cero.

### Componente de eventos conocidos

La medición será híbrida y conservará dos señales distintas:

```text
statistical_inflection_flag = 1 cuando movement_zscore >= 2.0
known_event_flag            = 1 cuando un evento aprobado aplica al alcance y al mes
major_inflection_flag       = máximo(statistical_inflection_flag, known_event_flag)
```

También debe conservarse el origen de la señal: `statistical`, `known_event` o `both`. Un evento localizado no debe marcar a toda la compañía; sólo aplica a la población perteneciente al alcance afectado en el snapshot correspondiente.

### Fechas candidatas encontradas en QGenie

La búsqueda en QGenie identificó los siguientes candidatos para construir y validar el calendario. Son puntos de partida, no un calendario completo ni autoritativo; las fechas efectivas y los alcances todavía deben confirmarse con el propietario del proceso.

| Fecha candidata | Evento o cambio identificado | Alcance inicial | Fuente encontrada |
|---|---|---|---|
| 2015-09-21 | Strategic Realignment Plan, Program Sycamore y Project Willow, incluyendo realineación organizacional y reducción de headcount | Amplio / compañía | `VP Briefing Slides 092115.pdf` |
| 2018-06-06 | Qualcomm 2.0 Engineering Restructuring y cambios organizacionales de Multimedia Core | Engineering / QCT / Multimedia, sujeto a mapping | `Multimedia Organizational Changes.pptx` y `Multimedia Organizational Changes r1.pptx` |
| 2023-05-11 | Multimedia Reorganization | Multimedia, sujeto a mapping | `Multimedia Reorg 5-11-23 v1.3.pdf` |

El candidato de 2015 queda fuera de la historia de snapshots actualmente documentada, que comienza el 2016-10-23, por lo que no puede contrastarse directamente con esa serie. Los eventos de 2018 y 2023 sí pueden utilizarse como fechas de contraste, después de confirmar el alcance organizacional y la fecha efectiva.

### Reglas time-safe y validaciones pendientes

- `known_event_flag` sólo puede activarse desde el primer snapshot en que el anuncio o la fecha efectiva ya era conocida; no se permite completar retrospectivamente snapshots anteriores con información futura.
- Deben validarse la semántica, fecha, observabilidad y consistencia de `manager_change`, `cost_center_change`, `job_family_change`, `location_change` e `is_transferred` y de sus fechas asociadas.
- Debe confirmarse el mapping histórico entre cada evento conocido y la población organizacional afectada.
- Deben probarse deduplicación, fronteras mensuales, nulos, eventos múltiples, scopes pequeños y el caso de desviación estándar cero.
- Las fechas candidatas deben compararse con los picos observados, pero esa coincidencia es evidencia de apoyo y no demuestra por sí sola la definición.
- Para cambiar los scores históricos se requiere un nuevo plan v4, SQL agregado guardado, reconciliación independiente de la fórmula y validación time-safe del join empleado-snapshot.

<!-- BEGIN evaluate-attrition-variable:major-inflection-points -->
## Conocimiento acumulado: Major inflection points

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:45:35-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Organization events
- **Relevancia:** Un composite de cambios mayores podría representar disrupción acumulada.

### Definición y fuente evaluadas

- **Definición vigente:** Evento organizacional autoritativo, por definir, que representa una reorganización o punto de inflexión material.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** manager_change, manager_change_date, cost_center_change, cost_center_change_date, job_family_change, job_family_change_date, location_change, location_change_date, is_transferred, transfer_date
- **Grain:** Proxy de evento organizacional

### Relaciones con el portafolio

- Major inflection points depende de Manager change.
- Major inflection points depende de Transfer within past year.
- Comparten is_transferred (shared_source_column).
- Comparten manager_change (shared_source_column).
- Comparten manager_change_date (shared_source_column).
- Comparten transfer_date (shared_source_column).
- Comparten count_window_time_since (shared_semantic_cue).
- Comparten flag_event (shared_semantic_cue).
- Comparten group_category_level (shared_semantic_cue).
- Comparten manager_team_layers (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Media - utilizable con trabajo (9 puntos).
- **Scores:** Source=2, Definition=0, Coverage=2, Missingness=2, Consistency=0, History=2, Join=1, Effort=0
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_42_major-inflection-points_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_42_major-inflection-points_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_42_major-inflection-points_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_42_major-inflection-points_manager-change_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_42_major-inflection-points_cost-center-change_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_42_major-inflection-points_job-family-change_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_42_major-inflection-points_location-change_report_top_values.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_42_major-inflection-points_is-transferred_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:major-inflection-points -->
