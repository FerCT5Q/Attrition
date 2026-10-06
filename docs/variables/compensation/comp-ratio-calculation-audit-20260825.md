# Auditoría de cálculo de Comp ratio

Fecha de ejecución: `2026-08-25`  
Fecha de conocimiento: no usar snapshots posteriores a `2026-08-25`.

## Pregunta

¿La fórmula de `Comp ratio` está confirmada para el campo mensual de empleados y, si no, qué evidencia existe en fuentes relacionadas?

Tipo semántico: `precomputed_metric`.  
Grain objetivo: empleado-snapshot mensual.  
Población objetivo: `worker_type = 'Employee'`, `employee_type = 'Regular'`, `active_status = 1`, con `fis_mo_end_dt <= '2026-08-25'`.

Regla de aceptación para confirmar el campo objetivo: debe existir lineage autoritativo o una reconciliación independiente sobre la misma población, con numerador, denominador, unidad/moneda, fecha efectiva, redondeo y tolerancia definidos. La disponibilidad de campos o una distribución plausible no es suficiente.

## Fuente objetivo

La fuente es `hrda.post_hire_monthly_worker_dtls.compa_ratio`, de tipo `numeric(10,4)`. Las vistas `hrda.worker_details_latest` y `hrda.worker_snapshot_vw` lo transportan desde la fuente de empleados; no aparece una transformación del ratio en esas vistas.

La tabla mensual sí expone campos de pago y contexto: `annual_base_pay`, `base_pay_rate`, `total_base_pay_amount`, `fte_annual_base_pay`, `base_pay_frequency`, `fte_annual_base_pay_currency_code`, `compensation_grade`, `compensation_grade_old`, `compensation_grade_profile`, `cf_ee_rf360_comp_grade`, `labor_market`, país/región, `job_code`, `job_title`, `job_family`, niveles y `fte`. No expone `midpoint`, `mid_payrange`, `min_payrange`, `max_payrange`, `market_rate`, `base_pay_amount` ni `base_pay_anualized_amt`, por lo que no se puede reconstruir la división estándar dentro de la misma población.

La auditoría de disponibilidad encontró 3,023,211 filas elegibles. Los cuatro campos monetarios y `fte` estuvieron poblados en todas; `base_pay_frequency` estuvo poblado en 2,942,296 filas, `labor_market` en 2,930,669 y `std_hours` en 1,088,082. La reconciliación algebraica encontró 99.10% de coincidencia entre `annual_base_pay` y `fte_annual_base_pay`, pero sólo 34.34% entre `annual_base_pay` y `base_pay_rate`, y 33.53% entre `annual_base_pay` y `total_base_pay_amount`. Esto apoya usar los dos primeros como hipótesis de numerador anual, pero no prueba la semántica ni el campo seleccionado por Workday.

Consultas: `queries/audits/comp_ratio_employee_component_inventory_20260825.sql`, `queries/audits/comp_ratio_employee_component_coverage_20260825.sql`, `queries/audits/comp_ratio_employee_pay_component_reconciliation_20260825.sql` y `queries/audits/comp_ratio_employee_column_comments_20260825.sql`.

No se encontró comentario útil de columna en `pg_catalog.pg_description`. La auditoría de rutinas de `hrda` encontró menciones del campo en procesos de copia/carga, pero ninguna asignación explícita de `compa_ratio = ...` ni una rutina de empleados que combine `compa_ratio` con `mid_payrange`. Las divisiones encontradas en otras rutinas no usan `mid_payrange` y no constituyen lineage del campo.

## Perfil agregado actual

Consulta: `queries/audits/comp_ratio_target_profile_20260825.sql`.

- 3,023,211 filas empleado-snapshot.
- 70,933 empleados distintos.
- 74 fechas de snapshot.
- 100.00% de filas pobladas.
- 0 grupos duplicados en la clave empleado-snapshot.
- Primer snapshot considerado: `2020-07-26`.
- Último snapshot considerado: `2026-08-23`.
- 95,395 valores no positivos en toda la ventana.
- 43 valores mayores que 3 en toda la ventana.

Consulta: `queries/audits/comp_ratio_target_latest_profile_20260825.sql`.

En `2026-08-23` hay 50,045 empleados elegibles; 849 valores no positivos (1.70%) y 2 mayores que 3. La consulta suprime bandas con menos de 30 empleados.

## Fuente de ofertas

`hrda.offers` contiene el campo `compa_ratio_base_pay` (`numeric(10,2)`) y sus componentes: `base_pay_amount` (`numeric(20,2)`), `base_pay_anualized_amt` (`numeric(20,2)`), `base_pay_amount_currency_code`, `base_pay_anualized_amt_currency_code`, `min_payrange`, `mid_payrange` y `max_payrange` (`numeric(10,2)`).

La vista `hrda.pre_hire_flat_and_wide_summary_mvw` es de tipo `VIEW`, tiene `employee_id`, fechas de oferta/contratación y esos campos de compensación, y los pasa desde `offers`. La vista no contiene la división; tampoco la contienen `hrda.offers_vw` ni `hrda.offers_snapshot`.

## Reconciliación de ofertas

Consulta: `queries/audits/comp_ratio_offers_formula_reconciliation_20260825.sql`.

Población: filas de `hrda.offers` con `employee_id` no nulo y `last_updated_date <= '2026-08-25'`. Se comparten sólo métricas agregadas.

- 55,516 filas y 44,859 empleados con el ratio de oferta poblado.
- 47,845 filas comparables y 41,458 empleados con `base_pay_amount` y `mid_payrange` válidos.
- 47,845 de 47,845 coincidieron dentro de `0.01`.
- 47,845 de 47,845 coincidieron exactamente después de redondear el cociente a dos decimales.
- La tasa de coincidencia fue 100.00% y no hubo mismatches bajo esa tolerancia.
- Usando `base_pay_anualized_amt / mid_payrange`, sólo 12,478 de 47,845 coincidieron dentro de `0.01` (26.08%).
- 7,671 filas tenían midpoint ausente o no positivo.

Resultado: la fórmula almacenada en `offers.compa_ratio_base_pay` queda fuertemente respaldada como `base_pay_amount / mid_payrange`, con redondeo a dos decimales. Esto es evidencia de la fuente de ofertas y no prueba la fórmula de `post_hire_monthly_worker_dtls.compa_ratio`.

## Prueba temporal contextual

Consulta: `queries/audits/comp_ratio_target_offer_temporal_reconciliation_20260825.sql`.

Regla exploratoria: deduplicar por empleado-candidato-fecha de contratación y unir al primer snapshot mensual de empleado regular activo dentro de los 45 días posteriores a `hire_date`.

- 53,773 filas de oferta antes de deduplicar; 44,304 empleados.
- 329 grupos de clave de oferta duplicados, con 669 filas.
- 44,104 ofertas únicas de 44,104 empleados después de excluir esas claves duplicadas.
- 34,437 ofertas encontraron un primer snapshot posterior; 9,667 no lo encontraron.
- 14,121 ofertas tenían más de un snapshot dentro de la ventana y se resolvieron al primero.
- 12,613 de 34,437 pares (36.63%) coincidieron con el ratio de oferta dentro de `0.01`.
- 12,406 de 34,437 pares (36.03%) coincidieron con `base_pay_amount / mid_payrange` dentro de `0.01`.

Resultado: la coincidencia parcial no es una reconciliación válida del campo mensual. Las fuentes tienen grain y momento distintos, y el ratio del empleado puede reflejar cambios posteriores a la oferta.

## Evidencia de negocio de QGenie

QGenie recuperó dos documentos del proyecto `TEAMS/ANNUALREVIEW_MGR`: `Rewards/Compa Ratio_Tip sheet.pdf` y `Rewards/Rewards Discussions_What to Say & What Not to Say.pdf`. Su definición de negocio es consistente: `Compa-Ratio = Employee Annualized Base Pay / Market Rate`, donde `Market Rate` es el midpoint o percentil 50 del mercado. También indican que el ratio se muestra como porcentaje en Workday, que 100% equivale al midpoint y que los rangos se revisan anualmente.

QGenie no identificó el nombre técnico del midpoint, la tabla de origen ni el lineage de `post_hire_monthly_worker_dtls.compa_ratio`. El material de Job Catalog recuperado menciona `Job Code`, `Job Title`, `Job Family`, `Job Level`, `Compensation Grade`, `Job Profile` y ubicación, lo que respalda esas columnas como posibles claves de contexto, no como el denominador.

Esta sección es evidencia contextual y de definición de negocio; no sustituye una reconciliación técnica sobre el campo mensual.

## Inventario de fully_loaded_cost

La tabla `hrda.fully_loaded_cost` contiene `midpoint_usd` y las claves `compensation_grade_profile`, `labor_market`, `compensation_grade`, `currency`, `country`, `job_code`, `job_title` y `job_family`, junto con `data_as_of`. Hasta la fecha de corte presentó 56,675 filas, cinco fechas de vigencia entre `2024-06-24` y `2026-08-04`, midpoint poblado y positivo en todas las filas, y una fila única por clave y fecha.

La reconciliación temporal con `post_hire_monthly_worker_dtls` empató 1,124,553 de 3,023,211 snapshots, un 37.20%. Usando la última versión `data_as_of` disponible antes del snapshot, la fórmula `annual_base_pay / midpoint_usd` coincidió con `compa_ratio` en 296,715 de 1,124,553 pares comparables, un 26.39%; el resultado fue idéntico con `fte_annual_base_pay`. Las 809,949 filas con más de una candidata representan versiones históricas previas de la misma clave. Por tanto, `midpoint_usd` no está validado como midpoint salarial del ratio mensual.

Consultas: `queries/audits/comp_ratio_fully_loaded_cost_schema_20260825.sql`, `queries/audits/comp_ratio_fully_loaded_cost_grain_audit_20260825.sql` y `queries/audits/comp_ratio_fully_loaded_cost_target_reconciliation_20260825.sql`.

## Conclusión

La base confirma cómo se calcula el **ratio de ofertas**, pero no cómo se calcula el **`Comp ratio` mensual de empleados**. Para el campo objetivo, la definición sigue siendo una métrica precalculada con fórmula, componentes y lineage pendientes. Bajo la puerta semántica de `evaluate-attrition-variable`, la definición no debe recibir score 2.

### Teoría no confirmada

La teoría de trabajo es que el campo mensual sigue la convención de compensación:

```text
compa_ratio = pago base comparable / midpoint del rango salarial aplicable
```

Es posible que el numerador sea `annual_base_pay` o `fte_annual_base_pay` y que el denominador provenga del rango asociado al grado, mercado, país, moneda, puesto y fecha efectiva. `base_pay_rate` y `total_base_pay_amount` no son sustitutos seguros porque sólo coinciden con `annual_base_pay` en una parte de las filas. Ninguna de esas alternativas está confirmada para `hrda.post_hire_monthly_worker_dtls.compa_ratio`; no debe usarse como definición oficial ni como regla de modelado sin lineage de HRIS/Compensation y una reconciliación sobre la población mensual.

## Seguimiento de lineage del dashboard FLC - 2026-08-27

Se revisó el workbook de Tableau `references/tableau/organizational-csi-dashboard/Organizational CSI Dashboard.twb`. La fuente FLC está definida como:

```sql
select * from hrda.fully_loaded_cost flc
where flc.last_modified_date = (select max(last_modified_date) from hrda.fully_loaded_cost)
```

El workbook une el employee feed con FLC usando únicamente `compensation_grade_profile` y `job_code`. También confirma que `compa_ratio` se trae directamente del employee feed y que `midpoint_usd` se trae de FLC. El campo calculado llamado `FLC` suma `midpoint_usd`, `bonus_allocation_usd` y `stock_allocation_usd`; no calcula el ratio salarial.

Se ejecutó la consulta agregada `queries/audits/comp_ratio_flc_dashboard_join_reconciliation_20260827.sql` sobre empleados regulares activos y snapshots hasta `2026-08-26`. La reproducción del join del dashboard encontró midpoint en 2,879,177 de 3,023,209 filas, un 95.24%, sin múltiples matches por clave. Sin embargo, `annual_base_pay / midpoint_usd` coincidió con el `compa_ratio` almacenado en 363,904 de 2,879,177 filas comparables, un 12.64%; el resultado fue igual usando `fte_annual_base_pay`.

Regla de aceptación: para considerar `midpoint_usd` como denominador del `compa_ratio` mensual, la fórmula debe reconciliarse en al menos 95% de la población comparable con join, fecha efectiva, moneda, FTE y redondeo definidos. Resultado: `outcome: fail`.

Conclusión: `hrda.fully_loaded_cost` queda confirmado como fuente del dashboard FLC y como fuente relacionada de `midpoint_usd`, pero no como denominador confirmado del `compa_ratio` mensual. El join del dashboard usa la carga más reciente y no restringe `data_as_of` al snapshot, por lo que tampoco es una ruta time-safe para reconstruir historia de attrition. Sigue pendiente el lineage oficial del midpoint usado por el campo mensual.
