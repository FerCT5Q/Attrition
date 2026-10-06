-- Talent index: consistencia estructural en el grain empleado-ciclo-version.
--
-- Claim:
--   Medir llaves faltantes, duplicados exactos, conflictos de valor y versiones
--   multiples antes de construir el join mensual.
--
-- Acceptance rule stated before execution for Consistency=2:
--   No debe haber llaves faltantes, duplicados exactos, conflictos de talent_index
--   ni fechas tecnicas faltantes; las versiones multiples deben tener una regla de
--   vigencia gobernada.

WITH base AS (
  SELECT
    CAST(empl_id AS BIGINT) AS employee_id,
    cycle_number,
    COALESCE(last_modified_date, airflow_execution_date) AS availability_date,
    talent_index,
    talent_quartile
  FROM hrda.master_talent_index
),
exact_keys AS (
  SELECT
    employee_id,
    cycle_number,
    availability_date,
    COUNT(*) AS source_rows,
    COUNT(DISTINCT talent_index) AS distinct_index_values
  FROM base
  WHERE employee_id IS NOT NULL
    AND cycle_number IS NOT NULL
  GROUP BY 1, 2, 3
),
employee_cycle AS (
  SELECT
    employee_id,
    cycle_number,
    MIN(availability_date) AS min_availability_date,
    MAX(availability_date) AS max_availability_date
  FROM base
  WHERE employee_id IS NOT NULL
    AND cycle_number IS NOT NULL
  GROUP BY 1, 2
),
base_metrics AS (
  SELECT
    COUNT(DISTINCT cycle_number) AS observations_checked,
    COUNT(*) AS source_rows,
    COUNT(CASE WHEN employee_id IS NULL THEN 1 END) AS rows_missing_employee_id,
    COUNT(CASE WHEN cycle_number IS NULL THEN 1 END) AS rows_missing_cycle_number,
    COUNT(CASE WHEN availability_date IS NULL THEN 1 END)
      AS rows_missing_availability_date,
    COUNT(CASE WHEN talent_index IS NULL THEN 1 END) AS rows_missing_talent_index,
    COUNT(CASE
      WHEN talent_quartile IS NOT NULL
       AND talent_quartile NOT BETWEEN 1 AND 5
      THEN 1
    END) AS quartile_outside_observed_1_to_5_rows
  FROM base
),
key_metrics AS (
  SELECT
    COUNT(CASE WHEN source_rows > 1 THEN 1 END) AS duplicate_key_groups,
    COALESCE(SUM(CASE WHEN source_rows > 1 THEN source_rows - 1 ELSE 0 END), 0)
      AS duplicate_rows,
    COUNT(CASE WHEN distinct_index_values > 1 THEN 1 END)
      AS conflicting_index_key_groups
  FROM exact_keys
),
cycle_metrics AS (
  SELECT
    COUNT(CASE
      WHEN min_availability_date <> max_availability_date THEN 1
    END) AS multi_version_employee_cycle_groups
  FROM employee_cycle
)
SELECT
  'Talent index' AS variable_name,
  base_metrics.observations_checked,
  base_metrics.source_rows,
  base_metrics.rows_missing_employee_id,
  base_metrics.rows_missing_cycle_number,
  base_metrics.rows_missing_availability_date,
  base_metrics.rows_missing_talent_index,
  base_metrics.quartile_outside_observed_1_to_5_rows,
  key_metrics.duplicate_key_groups,
  key_metrics.duplicate_rows,
  key_metrics.conflicting_index_key_groups,
  cycle_metrics.multi_version_employee_cycle_groups,
  (
    base_metrics.rows_missing_employee_id
    + base_metrics.rows_missing_cycle_number
    + base_metrics.rows_missing_availability_date
    + key_metrics.duplicate_key_groups
    + key_metrics.conflicting_index_key_groups
  ) AS anomaly_count
FROM base_metrics
CROSS JOIN key_metrics
CROSS JOIN cycle_metrics;
