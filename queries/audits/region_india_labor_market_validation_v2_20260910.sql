/*
  Triple-check de display: Region almacenada INDIA y labor_market.

  Claim: En el snapshot mensual 2026-08-23, los empleados activos regulares
  cuya Region almacenada es INDIA pertenecen a un único labor_market: IND.

  Población: worker_type='Employee', employee_type='Regular', active_status=1.
  Grain: empleado-snapshot distinto.
  Entrega: presentation; sólo métricas agregadas, sin identificadores.

  Regla de aceptación: población >= 30; exactamente una categoría de
  labor_market, con mínimo y máximo IND; cero empleados con varias filas fuente,
  varias Region o varios labor_market en el mismo snapshot.
*/
WITH source_rows AS (
  SELECT
    employee_id,
    region,
    labor_market
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE fis_mo_end_dt::date = DATE '2026-08-23'
    AND worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND region = 'INDIA'
),
per_employee AS (
  SELECT
    employee_id,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT region) AS distinct_region_count,
    COUNT(DISTINCT labor_market) AS distinct_labor_market_count,
    MIN(labor_market) AS labor_market
  FROM source_rows
  GROUP BY employee_id
)
SELECT
  COUNT(*) AS eligible_employees,
  COUNT(DISTINCT labor_market) AS labor_market_category_count,
  MIN(labor_market) AS minimum_labor_market,
  MAX(labor_market) AS maximum_labor_market,
  SUM(CASE WHEN source_row_count <> 1 THEN 1 ELSE 0 END) AS employees_with_multiple_source_rows,
  SUM(CASE WHEN distinct_region_count <> 1 THEN 1 ELSE 0 END) AS employees_with_conflicting_region_values,
  SUM(CASE WHEN distinct_labor_market_count <> 1 THEN 1 ELSE 0 END) AS employees_with_conflicting_labor_market_values
FROM per_employee;
