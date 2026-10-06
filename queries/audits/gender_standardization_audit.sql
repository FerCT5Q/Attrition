WITH base AS (
  SELECT
    employee_id,
    CAST(fis_mo_end_dt AS DATE) AS snapshot_date,
    CAST(gender AS VARCHAR(256)) AS raw_value,
    UPPER(TRIM(CAST(gender AS VARCHAR(256)))) AS normalized_value
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND active_status = 1
    AND fis_mo_end_dt IS NOT NULL
),
sequenced AS (
  SELECT
    employee_id,
    snapshot_date,
    raw_value,
    normalized_value,
    LAG(raw_value) OVER (
      PARTITION BY employee_id ORDER BY snapshot_date
    ) AS previous_raw_value,
    LAG(normalized_value) OVER (
      PARTITION BY employee_id ORDER BY snapshot_date
    ) AS previous_normalized_value
  FROM base
),
monthly AS (
  SELECT
    snapshot_date,
    COUNT(DISTINCT employee_id) AS eligible_employees,
    COUNT(DISTINCT CASE
      WHEN NULLIF(TRIM(raw_value), '') IS NOT NULL THEN employee_id
    END) AS observable_employees,
    SUM(CASE WHEN raw_value IS NULL THEN 1 ELSE 0 END) AS null_rows,
    SUM(CASE
      WHEN raw_value IS NOT NULL AND TRIM(raw_value) = '' THEN 1 ELSE 0
    END) AS blank_rows,
    COUNT(DISTINCT CASE
      WHEN NULLIF(TRIM(raw_value), '') IS NOT NULL THEN raw_value
    END) AS raw_distinct_count,
    COUNT(DISTINCT CASE
      WHEN normalized_value <> '' THEN normalized_value
    END) AS normalized_distinct_count,
    SUM(CASE
      WHEN raw_value IS NOT NULL AND raw_value <> TRIM(raw_value) THEN 1 ELSE 0
    END) AS whitespace_adjusted_rows,
    SUM(CASE
      WHEN NULLIF(TRIM(previous_raw_value), '') IS NOT NULL
       AND NULLIF(TRIM(raw_value), '') IS NOT NULL
       AND raw_value <> previous_raw_value
      THEN 1 ELSE 0
    END) AS raw_transition_rows,
    SUM(CASE
      WHEN NULLIF(previous_normalized_value, '') IS NOT NULL
       AND NULLIF(normalized_value, '') IS NOT NULL
       AND normalized_value <> previous_normalized_value
      THEN 1 ELSE 0
    END) AS normalized_transition_rows,
    SUM(CASE
      WHEN COALESCE(NULLIF(previous_normalized_value, ''), '__MISSING__')
        <> COALESCE(NULLIF(normalized_value, ''), '__MISSING__')
       AND (
         NULLIF(previous_normalized_value, '') IS NULL
         OR NULLIF(normalized_value, '') IS NULL
       )
      THEN 1 ELSE 0
    END) AS missing_state_transition_rows
  FROM sequenced
  GROUP BY snapshot_date
)
SELECT
  snapshot_date,
  eligible_employees,
  observable_employees,
  eligible_employees - observable_employees AS missing_employees,
  ROUND(
    100.0 * observable_employees / NULLIF(eligible_employees, 0),
    4
  ) AS observable_coverage_percent,
  null_rows,
  blank_rows,
  raw_distinct_count,
  normalized_distinct_count,
  raw_distinct_count - normalized_distinct_count AS normalization_collision_count,
  whitespace_adjusted_rows,
  raw_transition_rows,
  normalized_transition_rows,
  missing_state_transition_rows
FROM monthly
WHERE eligible_employees >= 30
ORDER BY snapshot_date
