-- Gender: auditoria agregada de dominio, cobertura, estabilidad y grain.
-- Poblacion: Employee / Regular / active_status=1.
-- Ventana: snapshots mensuales desde 2020-07-26 hasta el ultimo snapshot
-- cerrado al 2026-08-17.
-- Grain objetivo: empleado-snapshot mensual.
--
-- Reglas de aceptacion declaradas antes de ejecutar:
-- 1. La afirmacion tecnica "se observan dos codigos" pasa si existen
--    exactamente dos codigos normalizados en el total, en cada snapshot y
--    en el ultimo snapshot cerrado.
-- 2. Coverage pasa si todos los snapshots tienen al menos 95% de llaves
--    empleado-snapshot con un valor no vacio.
-- 3. La normalizacion pasa si no hay colisiones por TRIM/UPPER, whitespace
--    residual ni contradicciones dentro de una llave empleado-snapshot.
-- 4. El grain pasa si no existen llaves empleado-snapshot duplicadas.
-- 5. La privacidad de cohortes pasa si ninguna celda codigo-snapshot tiene
--    menos de 30 empleados. No se devuelven etiquetas ni distribuciones.

WITH base AS (
  SELECT
    employee_id,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(gender AS VARCHAR(256)) AS raw_value,
    NULLIF(TRIM(CAST(gender AS VARCHAR(256))), '') AS trimmed_value,
    UPPER(NULLIF(TRIM(CAST(gender AS VARCHAR(256))), '')) AS normalized_value
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt >= CAST('2020-07-26' AS DATE)
    AND fis_mo_end_dt <= CAST('2026-08-17' AS DATE)
),
key_level AS (
  SELECT
    employee_id,
    snapshot_date,
    COUNT(*) AS source_row_count,
    COUNT(DISTINCT normalized_value) AS normalized_values_in_key,
    MIN(normalized_value) AS representative_value
  FROM base
  GROUP BY employee_id, snapshot_date
),
monthly_domain AS (
  SELECT
    snapshot_date,
    COUNT(DISTINCT raw_value) AS raw_distinct_codes,
    COUNT(DISTINCT normalized_value) AS normalized_distinct_codes,
    SUM(CASE
      WHEN raw_value IS NOT NULL AND raw_value <> TRIM(raw_value) THEN 1
      ELSE 0
    END) AS whitespace_adjusted_rows
  FROM base
  GROUP BY snapshot_date
),
monthly_keys AS (
  SELECT
    snapshot_date,
    COUNT(*) AS eligible_keys,
    SUM(CASE WHEN normalized_values_in_key > 0 THEN 1 ELSE 0 END) AS populated_keys,
    SUM(CASE WHEN normalized_values_in_key = 0 THEN 1 ELSE 0 END) AS missing_keys,
    SUM(CASE WHEN normalized_values_in_key > 1 THEN 1 ELSE 0 END) AS contradictory_keys,
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_keys,
    SUM(CASE WHEN source_row_count > 1 THEN source_row_count - 1 ELSE 0 END) AS duplicate_extra_rows
  FROM key_level
  GROUP BY snapshot_date
),
monthly AS (
  SELECT
    d.snapshot_date,
    d.raw_distinct_codes,
    d.normalized_distinct_codes,
    d.whitespace_adjusted_rows,
    k.eligible_keys,
    k.populated_keys,
    k.missing_keys,
    k.contradictory_keys,
    k.duplicate_keys,
    k.duplicate_extra_rows,
    100.0 * k.populated_keys / NULLIF(k.eligible_keys, 0) AS coverage_percent
  FROM monthly_domain d
  JOIN monthly_keys k
    ON d.snapshot_date = k.snapshot_date
),
category_month AS (
  SELECT
    snapshot_date,
    representative_value,
    COUNT(*) AS employee_snapshot_keys
  FROM key_level
  WHERE normalized_values_in_key = 1
  GROUP BY snapshot_date, representative_value
),
sequenced AS (
  SELECT
    employee_id,
    snapshot_date,
    representative_value,
    LAG(representative_value) OVER (
      PARTITION BY employee_id ORDER BY snapshot_date
    ) AS previous_value
  FROM key_level
  WHERE normalized_values_in_key <= 1
),
transitions AS (
  SELECT
    SUM(CASE
      WHEN previous_value IS NOT NULL
       AND representative_value IS NOT NULL
       AND previous_value <> representative_value
      THEN 1 ELSE 0
    END) AS normalized_change_events,
    COUNT(DISTINCT CASE
      WHEN previous_value IS NOT NULL
       AND representative_value IS NOT NULL
       AND previous_value <> representative_value
      THEN employee_id
    END) AS employees_with_normalized_change
  FROM sequenced
),
overall AS (
  SELECT
    COUNT(*) AS eligible_source_rows,
    SUM(CASE WHEN normalized_value IS NOT NULL THEN 1 ELSE 0 END) AS populated_source_rows,
    COUNT(DISTINCT raw_value) AS raw_distinct_codes,
    COUNT(DISTINCT normalized_value) AS normalized_distinct_codes,
    SUM(CASE
      WHEN raw_value IS NOT NULL AND raw_value <> TRIM(raw_value) THEN 1
      ELSE 0
    END) AS whitespace_adjusted_rows
  FROM base
),
key_totals AS (
  SELECT
    COUNT(*) AS eligible_employee_snapshot_keys,
    SUM(CASE WHEN normalized_values_in_key > 0 THEN 1 ELSE 0 END) AS populated_employee_snapshot_keys,
    SUM(CASE WHEN normalized_values_in_key = 0 THEN 1 ELSE 0 END) AS missing_employee_snapshot_keys,
    SUM(CASE WHEN normalized_values_in_key > 1 THEN 1 ELSE 0 END) AS contradictory_employee_snapshot_keys,
    SUM(CASE WHEN source_row_count > 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_keys,
    SUM(CASE WHEN source_row_count > 1 THEN source_row_count - 1 ELSE 0 END) AS duplicate_extra_rows
  FROM key_level
),
monthly_summary AS (
  SELECT
    MIN(snapshot_date) AS first_snapshot_date,
    MAX(snapshot_date) AS latest_snapshot_date,
    COUNT(*) AS observations_checked,
    SUM(CASE WHEN normalized_distinct_codes = 2 THEN 1 ELSE 0 END) AS months_with_exactly_two_codes,
    SUM(CASE WHEN normalized_distinct_codes < 2 THEN 1 ELSE 0 END) AS months_with_fewer_than_two_codes,
    SUM(CASE WHEN normalized_distinct_codes > 2 THEN 1 ELSE 0 END) AS months_with_more_than_two_codes,
    MIN(normalized_distinct_codes) AS minimum_monthly_normalized_codes,
    MAX(normalized_distinct_codes) AS maximum_monthly_normalized_codes,
    MIN(coverage_percent) AS minimum_monthly_coverage_percent,
    MAX(coverage_percent) AS maximum_monthly_coverage_percent,
    SUM(contradictory_keys) AS contradictory_keys,
    SUM(duplicate_keys) AS duplicate_keys,
    SUM(duplicate_extra_rows) AS duplicate_extra_rows
  FROM monthly
),
latest AS (
  SELECT
    normalized_distinct_codes AS latest_normalized_distinct_codes,
    eligible_keys AS latest_eligible_keys,
    populated_keys AS latest_populated_keys,
    missing_keys AS latest_missing_keys,
    coverage_percent AS latest_coverage_percent
  FROM monthly
  WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM monthly)
),
privacy_summary AS (
  SELECT
    SUM(CASE WHEN employee_snapshot_keys < 30 THEN 1 ELSE 0 END) AS category_month_cohorts_below_30,
    SUM(CASE
      WHEN snapshot_date = (SELECT MAX(snapshot_date) FROM monthly)
       AND employee_snapshot_keys < 30
      THEN 1 ELSE 0
    END) AS latest_category_cohorts_below_30
  FROM category_month
)
SELECT
  CAST('2026-08-17' AS DATE) AS evaluation_date,
  m.first_snapshot_date,
  m.latest_snapshot_date,
  m.observations_checked,
  o.eligible_source_rows,
  o.populated_source_rows,
  k.eligible_employee_snapshot_keys,
  k.populated_employee_snapshot_keys,
  k.missing_employee_snapshot_keys,
  ROUND(
    100.0 * k.populated_employee_snapshot_keys
      / NULLIF(k.eligible_employee_snapshot_keys, 0),
    4
  ) AS overall_coverage_percent,
  ROUND(m.minimum_monthly_coverage_percent, 4) AS minimum_monthly_coverage_percent,
  ROUND(l.latest_coverage_percent, 4) AS latest_coverage_percent,
  o.raw_distinct_codes,
  o.normalized_distinct_codes,
  o.raw_distinct_codes - o.normalized_distinct_codes AS normalization_collision_count,
  o.whitespace_adjusted_rows,
  l.latest_normalized_distinct_codes,
  m.months_with_exactly_two_codes,
  m.months_with_fewer_than_two_codes,
  m.months_with_more_than_two_codes,
  m.minimum_monthly_normalized_codes,
  m.maximum_monthly_normalized_codes,
  k.contradictory_employee_snapshot_keys,
  k.duplicate_employee_snapshot_keys,
  k.duplicate_extra_rows,
  t.normalized_change_events,
  t.employees_with_normalized_change,
  p.category_month_cohorts_below_30,
  p.latest_category_cohorts_below_30,
  CASE
    WHEN o.normalized_distinct_codes = 2
     AND l.latest_normalized_distinct_codes = 2
     AND m.months_with_exactly_two_codes = m.observations_checked
    THEN 1 ELSE 0
  END AS exactly_two_codes_rule_pass,
  CASE
    WHEN m.minimum_monthly_coverage_percent >= 95 THEN 1 ELSE 0
  END AS coverage_rule_pass,
  CASE
    WHEN o.raw_distinct_codes = o.normalized_distinct_codes
     AND o.whitespace_adjusted_rows = 0
     AND k.contradictory_employee_snapshot_keys = 0
    THEN 1 ELSE 0
  END AS normalization_rule_pass,
  CASE
    WHEN k.duplicate_employee_snapshot_keys = 0 THEN 1 ELSE 0
  END AS grain_rule_pass,
  CASE
    WHEN p.category_month_cohorts_below_30 = 0 THEN 1 ELSE 0
  END AS privacy_cohort_rule_pass
FROM overall o
CROSS JOIN key_totals k
CROSS JOIN monthly_summary m
CROSS JOIN latest l
CROSS JOIN transitions t
CROSS JOIN privacy_summary p;
