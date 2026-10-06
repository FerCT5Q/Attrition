-- Gender: distribución anual agregada y anonimizada.
-- Población: empleados regulares activos.
-- Grain: empleado-snapshot mensual.
-- Ventana: snapshots cerrados entre 2020-07-26 y 2026-08-17.
-- Privacidad: no devuelve las etiquetas reales de gender y suprime cohortes < 30.

WITH base AS (
  SELECT
    CAST(fiscal_year AS VARCHAR(20)) AS fiscal_year,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    UPPER(NULLIF(TRIM(CAST(gender AS VARCHAR(256))), '')) AS normalized_value
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt >= CAST('2020-07-26' AS DATE)
    AND fis_mo_end_dt <= CAST('2026-08-17' AS DATE)
),
domain AS (
  SELECT
    normalized_value,
    DENSE_RANK() OVER (ORDER BY normalized_value) AS category_number
  FROM (
    SELECT DISTINCT normalized_value
    FROM base
    WHERE normalized_value IS NOT NULL
  ) d
),
employee_snapshot AS (
  SELECT
    fiscal_year,
    snapshot_date,
    employee_id,
    COUNT(DISTINCT normalized_value) AS values_in_key,
    MIN(normalized_value) AS normalized_value
  FROM base
  GROUP BY fiscal_year, snapshot_date, employee_id
),
year_totals AS (
  SELECT
    fiscal_year,
    COUNT(*) AS eligible_employee_snapshots,
    SUM(CASE WHEN values_in_key = 1 THEN 1 ELSE 0 END)
      AS populated_employee_snapshots,
    SUM(CASE WHEN values_in_key = 0 THEN 1 ELSE 0 END)
      AS missing_employee_snapshots,
    SUM(CASE WHEN values_in_key > 1 THEN 1 ELSE 0 END)
      AS contradictory_employee_snapshots,
    COUNT(DISTINCT CASE
      WHEN values_in_key = 1 THEN normalized_value
    END) AS observed_normalized_codes
  FROM employee_snapshot
  GROUP BY fiscal_year
),
year_category AS (
  SELECT
    e.fiscal_year,
    d.category_number,
    COUNT(*) AS category_employee_snapshots
  FROM employee_snapshot e
  JOIN domain d
    ON e.normalized_value = d.normalized_value
  WHERE e.values_in_key = 1
  GROUP BY e.fiscal_year, d.category_number
)
SELECT
  y.fiscal_year,
  'CODE_' || CAST(c.category_number AS VARCHAR(10)) AS anonymized_category,
  c.category_employee_snapshots,
  ROUND(
    100.0 * c.category_employee_snapshots
      / NULLIF(y.populated_employee_snapshots, 0),
    4
  ) AS percent_of_populated_employee_snapshots,
  y.eligible_employee_snapshots,
  y.populated_employee_snapshots,
  y.missing_employee_snapshots,
  ROUND(
    100.0 * y.populated_employee_snapshots
      / NULLIF(y.eligible_employee_snapshots, 0),
    4
  ) AS coverage_percent,
  y.observed_normalized_codes,
  y.contradictory_employee_snapshots
FROM year_category c
JOIN year_totals y
  ON c.fiscal_year = y.fiscal_year
WHERE c.category_employee_snapshots >= 30
ORDER BY y.fiscal_year, c.category_number;
