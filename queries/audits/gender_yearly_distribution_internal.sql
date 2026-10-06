-- Gender: distribución anual interna, agregada y con etiqueta almacenada.
-- Modo de entrega: internal_analysis; no reutilizar en una presentación.
-- Población: empleados regulares activos; grain: empleado-snapshot deduplicado.
-- Ventana: snapshots cerrados entre 2020-07-26 y 2026-08-17.
-- Privacidad: sólo buckets con n >= 30; no devuelve identidades ni filas individuales.

WITH base AS (
  SELECT
    CAST(fiscal_year AS VARCHAR(20)) AS fiscal_year,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    employee_id,
    UPPER(NULLIF(TRIM(CAST(gender AS VARCHAR(256))), '')) AS gender
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt >= CAST('2020-07-26' AS DATE)
    AND fis_mo_end_dt <= CAST('2026-08-17' AS DATE)
),
employee_snapshot AS (
  SELECT
    fiscal_year,
    snapshot_date,
    employee_id,
    COUNT(DISTINCT gender) AS values_in_snapshot,
    MIN(gender) AS gender
  FROM base
  GROUP BY fiscal_year, snapshot_date, employee_id
),
year_category AS (
  SELECT
    fiscal_year,
    gender,
    COUNT(DISTINCT employee_id) AS employee_count
  FROM employee_snapshot
  WHERE values_in_snapshot = 1
    AND gender IS NOT NULL
  GROUP BY fiscal_year, gender
),
year_totals AS (
  SELECT
    fiscal_year,
    COUNT(DISTINCT employee_id) AS populated_employees
  FROM employee_snapshot
  WHERE values_in_snapshot = 1
    AND gender IS NOT NULL
  GROUP BY fiscal_year
)
SELECT
  c.fiscal_year,
  c.gender,
  c.employee_count,
  ROUND(
    100.0 * c.employee_count / NULLIF(t.populated_employees, 0),
    4
  ) AS percent_of_populated_employees,
  t.populated_employees
FROM year_category c
JOIN year_totals t
  ON c.fiscal_year = t.fiscal_year
WHERE c.employee_count >= 30
ORDER BY c.fiscal_year, c.gender;
