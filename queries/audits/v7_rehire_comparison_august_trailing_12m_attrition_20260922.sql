/*
  Claim: each displayed fiscal-August cohort can be split into two mutually
  exclusive groups, Rehire and the complement Not a rehire, with comparable
  trailing-12-month voluntary attrition.

  Presentation aggregate only. One baseline row is reconstructed per employee
  at each fiscal-August snapshot before joining distinct voluntary events.
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
  SELECT
    CAST(employee_id AS BIGINT) AS employee_id,
    CAST(term_date AS DATE) AS term_date
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
    CASE WHEN baseline.is_rehire = 1 THEN 'Rehire' ELSE 'Not a rehire' END AS rehire_group,
    baseline.employee_id,
    baseline.source_row_count,
    MAX(CASE WHEN voluntary_events.employee_id IS NOT NULL THEN 1 ELSE 0 END) AS voluntary_attrition_target
  FROM baseline
  LEFT JOIN voluntary_events
    ON voluntary_events.employee_id = baseline.employee_id
   AND voluntary_events.term_date > baseline.baseline_snapshot_date
   AND voluntary_events.term_date <= baseline.outcome_cutoff_date
  GROUP BY 1, 2, 3, 4, 5, 6
)
SELECT
  fiscal_year,
  baseline_snapshot_date,
  outcome_cutoff_date,
  rehire_group,
  COUNT(*) AS baseline_employee_count,
  COUNT(DISTINCT employee_id) AS distinct_employee_count,
  SUM(voluntary_attrition_target) AS voluntary_exit_count,
  ROUND(100.0 * SUM(voluntary_attrition_target) / NULLIF(COUNT(*), 0), 4) AS trailing_12m_voluntary_attrition_rate_percent,
  SUM(CASE WHEN source_row_count <> 1 THEN 1 ELSE 0 END) AS duplicate_employee_snapshot_count
FROM outcomes
GROUP BY 1, 2, 3, 4
ORDER BY CAST(fiscal_year AS INTEGER), CASE WHEN rehire_group = 'Rehire' THEN 1 ELSE 2 END;
