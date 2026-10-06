# Compensation

## Compensation grade

El mapping observado entre `compensation_grade`, `job_level_primary_position`,
`level_grouped` y `management_level` esta documentado en
[compensation-grade-catalog.md](compensation-grade-catalog.md). El sufijo
numerico no es universal entre prefijos; la nota incluye los cambios
historicos del mapping y sus limites de autoridad.

La documentacion separa el mapping observado de una teoria de trabajo no
confirmada sobre los prefijos y sufijos. Esa teoria no debe usarse como
definicion oficial ni como regla de modelado sin aprobacion de HRIS/Compensation.

`compensation_grade` identifica la clasificación salarial asignada a la posición o empleado. Tiene cobertura histórica completa en la evaluación actual, pero sigue siendo información gobernada y sensible.

## Comp ratio

Hay dos campos relacionados que no deben mezclarse:

- **Campo objetivo para el modelo:** `hrda.post_hire_monthly_worker_dtls.compa_ratio`, tipo `numeric(10,4)`, en grain empleado-snapshot mensual.
- **Campo de ofertas:** `hrda.offers.compa_ratio_base_pay`, tipo `numeric(10,2)`, expuesto también por `hrda.pre_hire_flat_and_wide_summary_mvw`.

Para el campo objetivo, Redshift almacena un valor precalculado. La tabla mensual sí contiene `annual_base_pay`, `base_pay_rate`, `total_base_pay_amount`, `fte_annual_base_pay`, frecuencia y moneda, pero no contiene `midpoint`, `mid_payrange`, `min_payrange`, `max_payrange` ni otro campo explícito de `market_rate`. Tampoco encontramos comentario de columna, asignación explícita en las rutinas revisadas ni una vista que reconstruya la fórmula.

El inventario ampliado de la tabla encontró otros campos que pueden servir como componentes de contexto o claves de búsqueda, pero no como denominador por sí mismos: `compensation_grade`, `compensation_grade_old`, `compensation_grade_profile`, `cf_ee_rf360_comp_grade`, `labor_market`, `country`, `region`, `job_code`, `job_title`, `job_family`, `job_level_primary_position`, `level_grouped`, `management_level`, `fte` y `std_hours`. En la población de empleados regulares activos con `fis_mo_end_dt <= 2026-08-25` hubo 3,023,211 filas y los cuatro campos monetarios (`annual_base_pay`, `base_pay_rate`, `total_base_pay_amount`, `fte_annual_base_pay`) y `fte` estuvieron poblados en todas. `base_pay_frequency` estuvo poblado en 2,942,296 filas, `labor_market` en 2,930,669 y `std_hours` en 1,088,082. Véanse `queries/audits/comp_ratio_employee_component_inventory_20260825.sql` y `queries/audits/comp_ratio_employee_component_coverage_20260825.sql`.

La comparación algebraica no identifica todavía el significado de cada importe. `annual_base_pay` y `fte_annual_base_pay` coincidieron dentro de `0.01` en 99.10% de las filas comparables; `base_pay_rate` y `total_base_pay_amount` coincidieron con `annual_base_pay` sólo en 34.34% y 33.53%, respectivamente. Esto deja a `annual_base_pay`/`fte_annual_base_pay` como candidatos de numerador, pero no prueba cuál es el salario anualizado utilizado por Workday. La consulta es `queries/audits/comp_ratio_employee_pay_component_reconciliation_20260825.sql`.

## Evidencia de negocio de QGenie

QGenie recuperó documentación de `TEAMS/ANNUALREVIEW_MGR`, en particular `Rewards/Compa Ratio_Tip sheet.pdf` y `Rewards/Rewards Discussions_What to Say & What Not to Say.pdf`. Esas fuentes describen la definición de negocio como salario base anualizado del empleado dividido entre el `Market Rate`, entendido como el midpoint o percentil 50 del mercado. También indican que Workday lo muestra como porcentaje, que 100% representa el midpoint y que los rangos se revisan anualmente. Los documentos mencionan puesto, mercado, experiencia, desempeño y tiempo en posición como factores relacionados.

Esta evidencia confirma la hipótesis de negocio sobre numerador y denominador, pero no identifica el nombre técnico del campo que contiene el midpoint ni demuestra el lineage de `hrda.post_hire_monthly_worker_dtls.compa_ratio`. QGenie también devolvió material de Job Catalog con `Job Code`, `Job Title`, `Job Family`, `Job Level`, `Compensation Grade`, `Job Profile` y ubicación; esos campos sirven como posibles claves de contexto, no como midpoint.

## Candidato externo: fully_loaded_cost

`hrda.fully_loaded_cost` contiene `midpoint_usd` y claves que se parecen a las del empleado: `compensation_grade_profile`, `labor_market`, `compensation_grade`, `currency`, `country`, `job_code`, `job_title` y `job_family`, además de `data_as_of`. Hasta el corte había 56,675 filas, cinco fechas `data_as_of` entre `2024-06-24` y `2026-08-04`, midpoint poblado y positivo en todas, y una fila única por combinación de claves y fecha.

Sin embargo, una reconciliación temporal con la población mensual sólo empató 1,124,553 de 3,023,211 snapshots (37.20%). Después de elegir la versión más reciente disponible antes de cada snapshot, `annual_base_pay / midpoint_usd` coincidió con `compa_ratio` sólo en 296,715 de 1,124,553 pares comparables (26.39%); `fte_annual_base_pay / midpoint_usd` tuvo el mismo resultado. Las 809,949 filas con más de una candidata son versiones históricas de la misma clave, no duplicados simultáneos. Por ahora `midpoint_usd` no puede considerarse el denominador del campo mensual. Véanse `queries/audits/comp_ratio_fully_loaded_cost_grain_audit_20260825.sql` y `queries/audits/comp_ratio_fully_loaded_cost_target_reconciliation_20260825.sql`.

En la fuente `offers`, la reconciliación agregada sí es reproducible:

```text
compa_ratio_base_pay = base_pay_amount / mid_payrange
```

Con `last_updated_date <= 2026-08-25`, `base_pay_amount / mid_payrange` coincidió con `offers.compa_ratio_base_pay` dentro de `0.01` y después de redondear a dos decimales en 47,845 filas comparables de 41,458 empleados; la tasa de coincidencia fue 100.00%. La versión con `base_pay_anualized_amt / mid_payrange` sólo coincidió en 26.08%. Esto confirma la fórmula observada para el campo de ofertas, no para el campo mensual de empleados.

La vista `pre_hire_flat_and_wide_summary_mvw` es una vista de recruiting que pasa los campos desde `offers`; no calcula el ratio. Una prueba temporal exploratoria unió ofertas con el primer snapshot mensual activo posterior a `hire_date`: sólo 36.03% de 34,437 pares comparables coincidió con `base_pay_amount / mid_payrange` dentro de `0.01`. Esto impide usar la fuente de ofertas como sustituto del `compa_ratio` mensual sin reglas de fecha y lineage aprobadas.

**Conclusión actual:** no conocemos todavía la fórmula del `hrda.post_hire_monthly_worker_dtls.compa_ratio`. La definición del campo objetivo permanece como métrica precalculada con lineage y componentes pendientes; no debe recibir evidencia de score 2. La auditoría detallada está en [comp-ratio-calculation-audit-20260825.md](comp-ratio-calculation-audit-20260825.md).

## Calidad observada

En la población de empleados regulares activos, con snapshots hasta `2026-08-25`:

- Hay 3,023,211 filas empleado-snapshot, 70,933 empleados distintos y 74 snapshots.
- El campo está poblado en 100.00% de las filas y no hay duplicados en el grain empleado-snapshot.
- El snapshot más reciente disponible antes del corte es `2026-08-23`, con 50,045 empleados.
- En ese snapshot, 849 valores son cero o negativos (1.70%) y 2 son mayores que 3.
- En toda la historia hasta el corte, hay 95,395 valores no positivos y 43 mayores que 3.

Por ello se necesita una regla gobernada de validez y outliers. Para modelado y reporting se deben usar bandas o percentiles, no valores exactos.

## Within team compensation range

No existe una columna directa con este significado. Debe derivarse con:

- `compa_ratio`
- `compensation_grade`
- `manager_employee_id`
- `fis_mo_end_dt`

Antes de calcularla deben definirse “team”, la población comparable, tamaño mínimo y estadístico permitido. Comparar personas de grados o mercados no comparables produciría una señal incorrecta.

### DistribuciÃ³n descriptiva por equipo — corte 2026-08-23

Para la lÃ¡mina se aprobÃ³ una definiciÃ³n descriptiva concreta. No calcula una
posiciÃ³n individual ni emite un juicio de equidad: cuenta, para cada manager,
los grupos comparables de reportes directos cuya brecha de salario base
ajustado a FTE es de al menos 10%.

- **Equipo:** reportes directos regulares activos que comparten
  `manager_employee_id` en el mismo snapshot; el manager se excluye de sus
  propios grupos. `reg_non_intern_dir_reports > 0` es una comprobaciÃ³n de la
  relaciÃ³n, no la llave de membresÃ­a.
- **Grupo comparable:** mismo manager, `country`, `compensation_grade` y
  `fte_annual_base_pay_currency_code`.
- **Elegibilidad:** al menos dos reportes con esos campos y
  `fte_annual_base_pay` positivos. Los faltantes se excluyen sÃ³lo de su grupo;
  un manager sin ningÃºn grupo elegible queda como `No comparable groups`, no
  como cero.
- **Flag:** `max(fte_annual_base_pay) / min(fte_annual_base_pay) >= 1.10`.
  Es una seÃ±al de revisiÃ³n de brecha material, no una diferencia estadÃ­stica
  ni una conclusiÃ³n de inequidad salarial.

En el corte participaron 50,043 empleados regulares activos y 10,583 managers
con al menos un reporte directo regular activo. Hubo 7,780 managers con algÃºn
grupo comparable y 2,803 en el estado separado sin grupo comparable. Se
formaron 12,108 grupos elegibles; 5,602 (46.27%) superaron el umbral de 10%.
Los dos grÃ¡ficos usan como denominador los 7,780 managers comparables:

- Conteo de grupos marcados: 0 = 3,421 (43.97%), 1 = 3,355 (43.12%),
  2 = 821 (10.55%), 3 = 143 (1.84%) y 4â€“7 = 40 (0.51%).
- ProporciÃ³n de grupos marcados: 0% = 3,421 (43.97%), >0â€“<50% = 265
  (3.41%), 50â€“<75% = 1,414 (18.17%), 75â€“<100% = 50 (0.64%) y 100% =
  2,630 (33.80%).

Toda categorÃ­a mostrada cumple `n >= 30`; el bucket superior de conteos se
agrupÃ³ en 4â€“7 para no publicar categorÃ­as escasas. El JSON congelado no
conserva sueldos, IDs, paÃ­ses, grados, monedas, managers ni filas fuente.

**Trazabilidad:**

- AuditorÃ­a: `queries/audits/within_team_compensation_pay_spread_integrity_20260823.sql`.
- Perfil: `queries/profiles/within_team_compensation_pay_spread_distribution_20260823.sql`.
- Constructor: `tools/build_within_team_compensation_distribution_evidence.py`.
- Evidencia congelada: `output/distribution/json/within-team-compensation-pay-spread-evidence-20260910.json`.
- Refresco focalizado: `tools/build_distribution_html_v2.py --reporting-mode presentation --refresh-within-team-compensation-slide`.

La variable sigue siendo sensible/restringida. `fte_annual_base_pay` se usa
como normalizaciÃ³n operativa para esta descripciÃ³n, pero su lineage de negocio
no queda confirmado por esta visualizaciÃ³n; el score v4 histÃ³rico no cambia.

## Acciones pendientes

1. Obtener lineage oficial de Compensation/HRIS para `post_hire_monthly_worker_dtls.compa_ratio` y confirmar qué campo representa el salario base anualizado.
2. Confirmar si `fully_loaded_cost.midpoint_usd` es un midpoint salarial o un componente de fully loaded cost; sólo usarlo con una regla aprobada de claves, moneda y fecha efectiva.
3. Obtener el midpoint/rango aplicable y su regla de fecha, moneda, FTE y redondeo para la misma población mensual.
4. Aprobar reglas para valores no positivos y outliers.
5. Reconciliar la fórmula de forma agregada por snapshot y definir bandas o percentiles permitidos con cohort suppression.

<!-- BEGIN evaluate-attrition-variable:compensation-grade -->
## Conocimiento acumulado: Compensation grade

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:37:54-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Compensation
- **Relevancia:** El grado controla estructura de compensación, pero es información gobernada y puede codificar nivel.

### Definición y fuente evaluadas

- **Definición vigente:** Grado de compensación del empleado registrado en cada snapshot mensual.
- **Tipo semántico:** direct_field
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** compensation_grade
- **Grain:** Snapshot de empleado

### Relaciones con el portafolio

- Comparten compensation_grade (shared_source_column).
- Comparten group_category_level (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo. Resultado de la prueba: Pendiente.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones. Resultado de la prueba: Pendiente.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y confirmar la definición propiedad de negocio, el dominio y los casos límite del campo directo; guardar SQL agregado, regla previa y métricas de reconciliación.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_31_compensation-grade_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_31_compensation-grade_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_31_compensation-grade_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_31_compensation-grade_compensation-grade_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:compensation-grade -->

<!-- BEGIN evaluate-attrition-variable:comp-ratio -->
## Conocimiento acumulado: Comp ratio

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:38:21-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Compensation
- **Relevancia:** La posición relativa frente al rango salarial mide alineación de mercado sin publicar compensación exacta.

### Definición y fuente evaluadas

- **Definición vigente:** Compa-ratio precalculado en el snapshot, destinado a representar la posición del base pay frente al midpoint aplicable; numerador y denominador autoritativos siguen pendientes.
- **Tipo semántico:** precomputed_metric
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** compa_ratio
- **Grain:** Snapshot de empleado

### Relaciones con el portafolio

- La posición relativa dentro del equipo depende de una definición válida de Comp ratio.
- Within team compensation range depende de Comp ratio.
- Comparten compa_ratio (shared_source_column).
- Comparten ratio_rate_percent (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 100.0%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La definición no puede considerarse confirmada hasta obtener lineage autoritativo y una reconciliación independiente de fórmula, componentes y tolerancia. Resultado de la prueba: Pendiente.
- Coverage reciente cumplió el threshold del score. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta obtener lineage autoritativo y una reconciliación independiente de fórmula, componentes y tolerancia.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Aprobar la definición y obtener lineage autoritativo y una reconciliación independiente de fórmula, componentes y tolerancia; guardar SQL agregado, regla previa y métricas de reconciliación.
- No se requiere acción inmediata.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_32_comp-ratio_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_32_comp-ratio_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_32_comp-ratio_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_32_comp-ratio_compa-ratio_report_numeric_bands.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:comp-ratio -->

<!-- BEGIN evaluate-attrition-variable:within-team-compensation-range -->
## Conocimiento acumulado: Within team compensation range

_Actualizado por el assessment v4 `attrition-43-monthly-fiscal-20260816` el 2026-08-16T20:38:53-06:00._

### Contexto del problema

- **Problema:** Evaluar conjuntamente 43 variables de RH para construir un modelo longitudinal que prediga attrition a partir de snapshots históricos.
- **Decisión / caso de uso:** Seleccionar, definir y priorizar features time-safe para un modelo de attrition, conservando la evolución de cada empleado a través de snapshots y comparando disponibilidad, cobertura y estabilidad entre años.
- **Outcome:** Attrition voluntario ocurrido después del snapshot de predicción y antes del siguiente snapshot mensual.
- **Población:** Empleados regulares activos en cada snapshot mensual de predicción.
- **Límite de conocimiento:** Utilizar exclusivamente información disponible al cierre de cada snapshot mensual; ninguna señal posterior al snapshot puede entrar a la feature.
- **Rol de la variable:** Compensation
- **Relevancia:** La posición relativa dentro de un grupo comparable puede capturar compresión salarial o valores atípicos.

### Definición y fuente evaluadas

- **Definición vigente:** Posición relativa de compensación del empleado dentro del equipo de su manager en el snapshot.
- **Tipo semántico:** derived_feature
- **Tabla / fuente:** hrda.post_hire_monthly_worker_dtls
- **Columnas:** compa_ratio, compensation_grade, manager_employee_id
- **Grain:** Empleado dentro del equipo

### Relaciones con el portafolio

- La posición relativa dentro del equipo depende de una definición válida de Comp ratio.
- Within team compensation range depende de Comp ratio.
- Comparten compa_ratio (shared_source_column).
- Comparten compensation_grade (shared_source_column).
- Comparten manager_employee_id (shared_source_column).
- Comparten group_category_level (shared_semantic_cue).
- Comparten manager_team_layers (shared_semantic_cue).
- Comparten ratio_rate_percent (shared_semantic_cue).

### Resultado y evidencia agregada

- **Resultado:** Sensible / restringida (12 puntos).
- **Scores:** Source=2, Definition=1, Coverage=2, Missingness=2, Consistency=1, History=2, Join=1, Effort=1
- **Coverage reciente:** 99.998%.
- **Historia utilizable:** 72.0 meses.

**Hallazgos principales**

- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo. Resultado de la prueba: Pendiente.
- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage. Resultado de la prueba: Pendiente.
- Coverage reciente cumplió el threshold del score. Resultado de la prueba: Pendiente.

**Limitaciones vigentes**

- La definición no puede considerarse confirmada hasta aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage.
- La cobertura por sí sola no demuestra dominio válido, estabilidad temporal ni ausencia de contradicciones.
- La ruta de join es plausible, pero no se ha demostrado una correspondencia temporal única y completa en el grain objetivo.
- La variable requiere validación, transformación o reglas gobernadas antes de tratarse como SQL directo y resuelto.

**Acciones recomendadas**

- Ejecutar una reconciliación agregada con elegibles, matched, unmatched, duplicados y multi-match por empleado-fecha.
- Aprobar la definición y aprobar y reconciliar fórmula, ventana, deduplicación, casos límite y controles de leakage; guardar SQL agregado, regla previa y métricas de reconciliación.
- No se requiere acción inmediata.
- Ejecutar la validación longitudinal específica, explicar anomalías y documentar reglas de normalización o mapping.
- Implementar y probar la ruta descrita en el plan de análisis y repetir las validaciones ejecutables v4.

**SQL y evidencia trazable**

- `queries\profiles\attrition-43-monthly-fiscal-20260816_33_within-team-compensation-range_coverage.sql`
- `queries/audits/attrition_43_v4_source_availability_audit.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_33_within-team-compensation-range_report_metadata.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_33_within-team-compensation-range_report_column_profile.sql`
- `queries\profiles\attrition-43-monthly-fiscal-20260816_33_within-team-compensation-range_compensation-grade_report_top_values.sql`

> Este documento aporta contexto acumulativo: no habilita score 2 ni sustituye la revalidación de claim, población, grain, ventana y regla de aceptación.
<!-- END evaluate-attrition-variable:within-team-compensation-range -->
