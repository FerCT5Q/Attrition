-- Talent index: confirmacion de fuente y columnas requeridas.
--
-- Claim:
--   hrda.master_talent_index y los campos necesarios para identificar, fechar,
--   interpretar y unir el indice existen en una ruta read-only accesible.
--
-- Acceptance rule stated before execution:
--   missing_items = 0.

WITH required_columns AS (
  SELECT 'empl_id' AS column_name
  UNION ALL SELECT 'talent_index'
  UNION ALL SELECT 'cycle_number'
  UNION ALL SELECT 'cycle_name'
  UNION ALL SELECT 'last_modified_date'
  UNION ALL SELECT 'airflow_execution_date'
  UNION ALL SELECT 'perf'
  UNION ALL SELECT 'stock'
  UNION ALL SELECT 'bonus'
  UNION ALL SELECT 'promo_index'
  UNION ALL SELECT 'talent_quartile'
  UNION ALL SELECT 'ar_eligibility'
),
table_status AS (
  SELECT COUNT(*) AS table_items_found
  FROM information_schema.tables
  WHERE table_schema = 'hrda'
    AND table_name = 'master_talent_index'
),
column_status AS (
  SELECT
    COUNT(*) AS required_column_items,
    SUM(CASE WHEN c.column_name IS NOT NULL THEN 1 ELSE 0 END)
      AS column_items_found
  FROM required_columns r
  LEFT JOIN information_schema.columns c
    ON c.table_schema = 'hrda'
   AND c.table_name = 'master_talent_index'
   AND c.column_name = r.column_name
)
SELECT
  'Talent index' AS variable_name,
  1 + required_column_items AS required_items,
  table_items_found,
  column_items_found,
  (1 - table_items_found) + (required_column_items - column_items_found)
    AS missing_items
FROM table_status
CROSS JOIN column_status;
