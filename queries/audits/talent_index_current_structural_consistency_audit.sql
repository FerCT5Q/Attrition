-- Talent index: consistencia estructural actual en el grain empleado-ciclo.
--
-- Claim:
--   Medir llaves faltantes, duplicados, conflictos de talent_index y contradicciones
--   básicas entre cycle_number y cycle_name sin usar timestamps técnicos.
--
-- Acceptance rule stated before execution for a fully clean structure:
--   No debe haber llaves faltantes, duplicados, valores conflictivos dentro de una
--   llave ni contradicciones en el mapping número-nombre. Aunque la regla pase,
--   Consistency permanece limitada mientras no exista catálogo/versionado oficial.

WITH base AS (
  SELECT
    CAST(empl_id AS BIGINT) AS employee_id,
    cycle_number,
    NULLIF(TRIM(cycle_name), '') AS cycle_name,
    talent_index
  FROM hrda.master_talent_index
),
employee_cycle AS (
  SELECT
    employee_id,
    cycle_number,
    COUNT(*) AS source_rows,
    COUNT(talent_index) AS populated_index_rows,
    COUNT(DISTINCT talent_index) AS distinct_index_values
  FROM base
  WHERE employee_id IS NOT NULL
    AND cycle_number IS NOT NULL
  GROUP BY 1, 2
),
cycle_number_mapping AS (
  SELECT
    cycle_number,
    COUNT(DISTINCT cycle_name) AS distinct_cycle_names
  FROM base
  WHERE cycle_number IS NOT NULL
    AND cycle_name IS NOT NULL
  GROUP BY 1
),
cycle_name_mapping AS (
  SELECT
    cycle_name,
    COUNT(DISTINCT cycle_number) AS distinct_cycle_numbers
  FROM base
  WHERE cycle_number IS NOT NULL
    AND cycle_name IS NOT NULL
  GROUP BY 1
),
employee_cycle_counts AS (
  SELECT
    employee_id,
    COUNT(DISTINCT cycle_number) AS cycle_count
  FROM base
  WHERE employee_id IS NOT NULL
    AND cycle_number IS NOT NULL
  GROUP BY 1
),
base_metrics AS (
  SELECT
    COUNT(DISTINCT cycle_number) AS observations_checked,
    COUNT(*) AS source_rows,
    COUNT(CASE WHEN employee_id IS NULL THEN 1 END) AS rows_missing_employee_id,
    COUNT(CASE WHEN cycle_number IS NULL THEN 1 END) AS rows_missing_cycle_number,
    COUNT(CASE WHEN cycle_name IS NULL THEN 1 END) AS rows_missing_cycle_name,
    COUNT(CASE WHEN talent_index IS NULL THEN 1 END) AS rows_missing_talent_index
  FROM base
),
key_metrics AS (
  SELECT
    COUNT(CASE WHEN source_rows > 1 THEN 1 END) AS duplicate_key_groups,
    COALESCE(SUM(CASE WHEN source_rows > 1 THEN source_rows - 1 ELSE 0 END), 0)
      AS duplicate_rows,
    COUNT(CASE
      WHEN distinct_index_values > 1
        OR (populated_index_rows > 0 AND populated_index_rows < source_rows)
      THEN 1
    END) AS conflicting_index_key_groups
  FROM employee_cycle
),
mapping_metrics AS (
  SELECT
    (
      SELECT COUNT(*)
      FROM cycle_number_mapping
      WHERE distinct_cycle_names > 1
    ) AS cycle_numbers_with_multiple_names,
    (
      SELECT COUNT(*)
      FROM cycle_name_mapping
      WHERE distinct_cycle_numbers > 1
    ) AS cycle_names_with_multiple_numbers
),
employee_metrics AS (
  SELECT
    COUNT(*) AS source_employees,
    COUNT(CASE WHEN cycle_count > 1 THEN 1 END) AS employees_with_multiple_cycles
  FROM employee_cycle_counts
)
SELECT
  'Talent index' AS variable_name,
  base_metrics.observations_checked,
  base_metrics.source_rows,
  employee_metrics.source_employees,
  employee_metrics.employees_with_multiple_cycles,
  base_metrics.rows_missing_employee_id,
  base_metrics.rows_missing_cycle_number,
  base_metrics.rows_missing_cycle_name,
  base_metrics.rows_missing_talent_index,
  key_metrics.duplicate_key_groups,
  key_metrics.duplicate_rows,
  key_metrics.conflicting_index_key_groups,
  mapping_metrics.cycle_numbers_with_multiple_names,
  mapping_metrics.cycle_names_with_multiple_numbers,
  (
    base_metrics.rows_missing_employee_id
    + base_metrics.rows_missing_cycle_number
    + key_metrics.duplicate_key_groups
    + key_metrics.conflicting_index_key_groups
    + mapping_metrics.cycle_numbers_with_multiple_names
    + mapping_metrics.cycle_names_with_multiple_numbers
  ) AS anomaly_count
FROM base_metrics
CROSS JOIN key_metrics
CROSS JOIN mapping_metrics
CROSS JOIN employee_metrics;

