-- Gender: seguimiento agregado de aliases de formato.
-- No devuelve etiquetas, IDs ni distribuciones por categoria.
--
-- Regla previa:
-- - Un alias de formato puede resolverse con UPPER(TRIM()) si no crea
--   contradicciones dentro de empleado-snapshot.
-- - Una cadena vacia no es una categoria: se clasifica como missing.
-- - Los cambios longitudinales se miden en el audit principal. Cualquier
--   cambio normalizado requiere interpretacion de negocio; sin una politica
--   gobernada no demuestra error ni habilita Consistency=2.

WITH base AS (
  SELECT
    employee_id,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(gender AS VARCHAR(256)) AS raw_value,
    UPPER(NULLIF(TRIM(CAST(gender AS VARCHAR(256))), '')) AS normalized_value
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt >= CAST('2020-07-26' AS DATE)
    AND fis_mo_end_dt <= CAST('2026-08-17' AS DATE)
),
alias_by_normalized_code AS (
  SELECT
    normalized_value,
    COUNT(DISTINCT raw_value) AS raw_alias_count
  FROM base
  WHERE normalized_value IS NOT NULL
  GROUP BY normalized_value
),
monthly_alias AS (
  SELECT
    snapshot_date,
    SUM(CASE WHEN raw_value IS NULL THEN 1 ELSE 0 END) AS null_rows,
    SUM(CASE
      WHEN raw_value IS NOT NULL AND TRIM(raw_value) = '' THEN 1 ELSE 0
    END) AS blank_rows,
    SUM(CASE
      WHEN raw_value IS NOT NULL
       AND raw_value <> UPPER(TRIM(raw_value))
      THEN 1 ELSE 0
    END) AS case_adjusted_rows,
    COUNT(DISTINCT CASE
      WHEN raw_value IS NOT NULL
       AND raw_value <> UPPER(TRIM(raw_value))
      THEN raw_value
    END) AS case_adjusted_raw_codes,
    COUNT(DISTINCT raw_value) - COUNT(DISTINCT normalized_value)
      AS normalization_collision_count
  FROM base
  GROUP BY snapshot_date
),
alias_summary AS (
  SELECT
    SUM(CASE WHEN raw_alias_count > 1 THEN 1 ELSE 0 END)
      AS normalized_codes_with_multiple_raw_aliases,
    MAX(raw_alias_count) AS maximum_raw_aliases_for_one_normalized_code
  FROM alias_by_normalized_code
),
monthly_summary AS (
  SELECT
    SUM(null_rows) AS null_rows,
    SUM(blank_rows) AS blank_rows,
    SUM(CASE WHEN null_rows > 0 THEN 1 ELSE 0 END) AS snapshots_with_nulls,
    SUM(CASE WHEN blank_rows > 0 THEN 1 ELSE 0 END) AS snapshots_with_blanks,
    MIN(CASE WHEN blank_rows > 0 THEN snapshot_date END)
      AS first_blank_snapshot,
    MAX(CASE WHEN blank_rows > 0 THEN snapshot_date END)
      AS latest_blank_snapshot,
    SUM(case_adjusted_rows) AS case_adjusted_rows,
    MAX(case_adjusted_raw_codes) AS maximum_case_adjusted_raw_codes_in_a_snapshot,
    SUM(CASE WHEN case_adjusted_rows > 0 THEN 1 ELSE 0 END)
      AS snapshots_with_case_adjustments,
    MIN(CASE WHEN case_adjusted_rows > 0 THEN snapshot_date END)
      AS first_case_adjustment_snapshot,
    MAX(CASE WHEN case_adjusted_rows > 0 THEN snapshot_date END)
      AS latest_case_adjustment_snapshot,
    SUM(CASE WHEN normalization_collision_count > 0 THEN 1 ELSE 0 END)
      AS snapshots_with_normalization_collision
  FROM monthly_alias
)
SELECT
  m.null_rows,
  m.blank_rows,
  m.snapshots_with_nulls,
  m.snapshots_with_blanks,
  m.first_blank_snapshot,
  m.latest_blank_snapshot,
  m.case_adjusted_rows,
  m.maximum_case_adjusted_raw_codes_in_a_snapshot,
  m.snapshots_with_case_adjustments,
  m.first_case_adjustment_snapshot,
  m.latest_case_adjustment_snapshot,
  m.snapshots_with_normalization_collision,
  a.normalized_codes_with_multiple_raw_aliases,
  a.maximum_raw_aliases_for_one_normalized_code,
  CASE
    WHEN a.normalized_codes_with_multiple_raw_aliases > 0
    THEN 1 ELSE 0
  END AS case_normalization_needed
FROM monthly_summary m
CROSS JOIN alias_summary a;
