/*
  Claim: each displayed Rehire annual rate is measured from the active-Regular
  Rehire cohort at the fiscal August closing snapshot and follows that same
  cohort through the next fiscal August closing snapshot.

  Internal analysis, aggregate-only. The result deliberately uses a distinct
  employee baseline for each fiscal closing, rather than FY-to-date exposure.
  Publish when the baseline cohort is at least 30 employees.
*/
WITH windows AS (
  SELECT '2024' AS fiscal_year, DATE '2023-08-20' AS baseline_snapshot_date, DATE '2024-08-25' AS outcome_cutoff_date
  UNION ALL SELECT '2025', DATE '2024-08-25', DATE '2025-08-24'
  UNION ALL SELECT '2026', DATE '2025-08-24', DATE '2026-08-23'
),
baseline AS (
  SELECT
    windows.fiscal_year,
    windows.baseline_snapshot_date,
    windows.outcome_cutoff_date,
    CAST(w.employee_id AS BIGINT) AS employee_id,
    MAX(COALESCE(w.is_rehire, 0)) AS is_rehire,
    COUNT(*) AS source_row_count
  FROM windows
  INNER JOIN hrda.post_hire_monthly_worker_dtls AS w
    ON CAST(w.fis_mo_end_dt AS DATE) = windows.baseline_snapshot_date
  WHERE w.worker_type = 'Employee'
    AND w.employee_type = 'Regular'
    AND w.active_status = 1
    AND w.employee_id IS NOT NULL
  GROUP BY 1, 2, 3, 4
),
voluntary_events AS (
  SELECT CAST(employee_id AS BIGINT) AS employee_id, CAST(term_date AS DATE) AS term_date
  FROM hrda.post_hire_monthly_worker_dtls
  WHERE worker_type = 'Employee'
    AND employee_type = 'Regular'
    AND UPPER(NULLIF(TRIM(CAST(term_type AS VARCHAR(128))), '')) = 'VOLUNTARY'
    AND term_date IS NOT NULL
  GROUP BY 1, 2
),
outcomes AS (
  SELECT
    baseline.fiscal_year,
    baseline.baseline_snapshot_date,
    baseline.outcome_cutoff_date,
    baseline.employee_id,
    MAX(CASE WHEN voluntary_events.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
  FROM baseline
  LEFT JOIN voluntary_events
    ON voluntary_events.employee_id = baseline.employee_id
   AND voluntary_events.term_date > baseline.baseline_snapshot_date
   AND voluntary_events.term_date <= baseline.outcome_cutoff_date
  WHERE baseline.is_rehire = 1
  GROUP BY 1, 2, 3, 4
),
baseline_quality AS (
  SELECT
    fiscal_year,
    SUM(CASE WHEN source_row_count <> 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count
  FROM baseline
  GROUP BY 1
)
SELECT
  outcomes.fiscal_year,
  outcomes.baseline_snapshot_date,
  outcomes.outcome_cutoff_date,
  COUNT(*) AS baseline_rehire_employee_count,
  COUNT(DISTINCT outcomes.employee_id) AS distinct_employee_count,
  SUM(outcomes.voluntary_attrition_target) AS voluntary_exit_count,
  ROUND(100.0 * SUM(outcomes.voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS trailing_12m_voluntary_attrition_rate_percent,
  baseline_quality.duplicate_employee_snapshot_count
FROM outcomes
INNER JOIN baseline_quality
  ON baseline_quality.fiscal_year = outcomes.fiscal_year
GROUP BY 1, 2, 3, 8
ORDER BY CAST(outcomes.fiscal_year AS INTEGER);
